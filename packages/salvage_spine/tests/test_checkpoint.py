from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path

import pytest

import packages.salvage_spine.checkpoint as checkpoint_module
from packages.salvage_spine.checkpoint import (
    Checkpoint,
    CheckpointIntegrityError,
    append_checkpoint,
    load_latest_checkpoint,
)
from packages.salvage_spine.models import canonical_json_bytes


def _checkpoint(**overrides: object) -> Checkpoint:
    data: dict[str, object] = {
        "schema_version": "1.0.0",
        "sequence": 0,
        "previous_digest": None,
        "state_id": "capsule-state-1",
        "phase": "capture-complete",
        "input_shas": {
            "remote_main": "1" * 40,
        },
        "capsule_root": "3" * 64,
        "manifest_digest": "4" * 64,
        "verification_digest": None,
        "completed_actions": ("captured-six-planes", "sealed-capsule"),
        "blockers": ("restore-pending", "human-review-pending"),
        "human_decisions": ("preserve-read-only-first", "stop-before-github"),
        "next_safe_command": "python -m pytest packages/salvage_spine/tests -q",
        "recovery_command": "python scripts/rebuild_capsule.py --state capsule-state-1",
        "digest": None,
    }
    data.update(overrides)
    return Checkpoint(**data)


def _next_checkpoint(previous: Checkpoint, **overrides: object) -> Checkpoint:
    data = asdict(previous)
    data.update(
        {
            "sequence": previous.sequence + 1,
            "previous_digest": previous.digest,
            "phase": "restore-complete",
            "completed_actions": (
                "captured-six-planes",
                "sealed-capsule",
                "restored-clean-room",
            ),
            "blockers": ("operator-approval-pending",),
            "human_decisions": (
                "preserve-read-only-first",
                "clean-room-restore-complete",
            ),
            "next_safe_command": "python -m pytest packages/salvage_spine/tests/test_restore.py -q",
            "recovery_command": "python scripts/replay_checkpoint.py --latest",
            "digest": None,
        }
    )
    data.update(overrides)
    return Checkpoint(**data)


def _verified_checkpoint(
    previous: Checkpoint,
    verification_digest: str = "5" * 64,
    **overrides: object,
) -> Checkpoint:
    data = asdict(_next_checkpoint(previous))
    data["verification_digest"] = verification_digest
    data["digest"] = None
    data.update(overrides)
    return Checkpoint(**data)


def _record_payload_digest(record: dict[str, object]) -> str:
    payload = {key: value for key, value in record.items() if key != "digest"}
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _record_bytes(record: dict[str, object]) -> bytes:
    materialized = copy.deepcopy(record)
    if materialized.get("digest") is None:
        materialized["digest"] = _record_payload_digest(materialized)
    return canonical_json_bytes(materialized)


def _write_chain(path: Path, *records: dict[str, object]) -> None:
    path.write_bytes(b"".join(_record_bytes(record) for record in records))


def _tampered_checkpoint_bytes(
    path: Path,
    *,
    line_index: int,
    old: str,
    new: str,
) -> bytes:
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[line_index] = lines[line_index].replace(old, new, 1)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _link_or_skip(source: Path, target: Path, *, symbolic: bool) -> None:
    try:
        if symbolic:
            os.symlink(source, target)
        else:
            os.link(source, target)
    except (AttributeError, NotImplementedError, OSError) as exc:
        pytest.skip(f"link creation unavailable: {exc}")


def _intent_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.append-intent.json")


def _write_intent(path: Path, committed: bytes, pending: Checkpoint) -> None:
    record = json.loads(canonical_json_bytes(pending))
    intent = {
        "schema_version": "1.0.0",
        "checkpoint_file": path.name,
        "committed_size": len(committed),
        "committed_sha256": hashlib.sha256(committed).hexdigest(),
        "pending_record": record,
        "pending_record_sha256": hashlib.sha256(
            canonical_json_bytes(record)
        ).hexdigest(),
    }
    _intent_path(path).write_bytes(canonical_json_bytes(intent))


class _FaultyAppendStream:
    def __init__(
        self,
        stream,
        *,
        write_actions: list[tuple[str, int | None]] | None = None,
        flush_error: BaseException | None = None,
    ) -> None:
        self._stream = stream
        self._write_actions = list(write_actions or [])
        self._flush_error = flush_error

    def write(self, data: bytes) -> int:
        if not self._write_actions:
            return self._stream.write(data)
        kind, value = self._write_actions.pop(0)
        if kind == "short":
            amount = value if value is not None else max(1, len(data) // 3)
            return self._stream.write(data[:amount])
        if kind == "zero":
            return 0
        if kind == "raise-after-partial":
            amount = value if value is not None else max(1, len(data) // 3)
            self._stream.write(data[:amount])
            raise OSError("injected partial-write failure")
        raise AssertionError(f"unknown write action: {kind}")

    def flush(self) -> None:
        if self._flush_error is not None:
            raise self._flush_error
        self._stream.flush()

    def __getattr__(self, name: str):
        return getattr(self._stream, name)


def _inject_faulty_fdopen(
    monkeypatch: pytest.MonkeyPatch,
    *,
    write_actions: list[tuple[str, int | None]] | None = None,
    flush_error: BaseException | None = None,
) -> None:
    original_fdopen = checkpoint_module.os.fdopen

    def wrapped_fdopen(fd: int, mode: str = "r", *args, **kwargs):
        stream = original_fdopen(fd, mode, *args, **kwargs)
        if mode == "r+b":
            return _FaultyAppendStream(
                stream,
                write_actions=write_actions,
                flush_error=flush_error,
            )
        return stream

    monkeypatch.setattr(checkpoint_module.os, "fdopen", wrapped_fdopen)


def test_checkpoint_chain_detects_rewrite(tmp_path: Path) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    append_checkpoint(path, second)

    path.write_bytes(
        _tampered_checkpoint_bytes(
            path,
            line_index=0,
            old="capture-complete",
            new="capture-altered",
        )
    )

    with pytest.raises(CheckpointIntegrityError, match="digest|canonical|chain"):
        load_latest_checkpoint(path)


def test_append_and_load_latest_preserve_canonical_chain(tmp_path: Path) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    append_checkpoint(path, second)

    assert path.read_bytes() == canonical_json_bytes(first) + canonical_json_bytes(
        second
    )
    assert b"\r\n" not in path.read_bytes()
    assert load_latest_checkpoint(path) == second
    assert load_latest_checkpoint(path).completed_actions == (
        "captured-six-planes",
        "sealed-capsule",
        "restored-clean-room",
    )
    assert load_latest_checkpoint(path).human_decisions == (
        "preserve-read-only-first",
        "clean-room-restore-complete",
    )


@pytest.mark.parametrize("line_index", [0, 1])
def test_load_rejects_rewrites_of_first_and_middle_records(
    tmp_path: Path,
    line_index: int,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first, phase="restore-complete")
    third = _next_checkpoint(second, phase="verification-complete")

    append_checkpoint(path, first)
    append_checkpoint(path, second)
    append_checkpoint(path, third)

    path.write_bytes(
        _tampered_checkpoint_bytes(
            path,
            line_index=line_index,
            old="complete",
            new="tampered",
        )
    )

    with pytest.raises(CheckpointIntegrityError):
        load_latest_checkpoint(path)


@pytest.mark.parametrize(
    ("name", "payload"),
    [
        ("truncated", b'{"sequence":0'),
        ("blank-line", b'{"a":1}\n\n'),
        ("malformed-json", b'{"sequence":0,]\n'),
        ("trailing-garbage", b'{"sequence":0} trailing\n'),
        ("crlf", b'{"sequence":0}\r\n'),
    ],
)
def test_load_rejects_malformed_blank_truncated_and_noncanonical_bytes(
    tmp_path: Path,
    name: str,
    payload: bytes,
) -> None:
    path = tmp_path / f"{name}.jsonl"
    path.write_bytes(payload)

    with pytest.raises(CheckpointIntegrityError):
        load_latest_checkpoint(path)


def test_load_missing_and_empty_path_behavior_is_explicit(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    with pytest.raises(FileNotFoundError):
        load_latest_checkpoint(missing)

    empty = tmp_path / "empty.jsonl"
    empty.write_bytes(b"")
    with pytest.raises(CheckpointIntegrityError, match="empty"):
        load_latest_checkpoint(empty)
    with pytest.raises(CheckpointIntegrityError, match="empty"):
        append_checkpoint(empty, _checkpoint())


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ("gap", "sequence"),
        ("duplicate", "sequence"),
        ("out-of-order", "sequence"),
        ("previous-digest", "previous_digest"),
        ("forged-digest", "digest"),
    ],
)
def test_load_rejects_sequence_and_digest_chain_violations(
    tmp_path: Path,
    mutation: str,
    match: str,
) -> None:
    path = tmp_path / f"{mutation}.jsonl"
    first = asdict(_checkpoint())
    second = asdict(_next_checkpoint(_checkpoint()))

    if mutation == "gap":
        second["sequence"] = 2
        second["previous_digest"] = first["digest"]
        second["digest"] = _record_payload_digest(second)
    elif mutation == "duplicate":
        second["sequence"] = 0
        second["previous_digest"] = None
        second["digest"] = _record_payload_digest(second)
    elif mutation == "out-of-order":
        first["sequence"] = 1
        first["previous_digest"] = "f" * 64
        first["digest"] = _record_payload_digest(first)
    elif mutation == "previous-digest":
        second["previous_digest"] = "f" * 64
        second["digest"] = _record_payload_digest(second)
    elif mutation == "forged-digest":
        second["digest"] = "0" * 64

    _write_chain(path, first, second)

    with pytest.raises(CheckpointIntegrityError, match=match):
        load_latest_checkpoint(path)


@pytest.mark.parametrize(
    ("sequence", "previous_digest"),
    [
        (1, None),
        (0, "f" * 64),
    ],
)
def test_first_record_requires_genesis_invariant(
    tmp_path: Path,
    sequence: int,
    previous_digest: str | None,
) -> None:
    path = tmp_path / "genesis.jsonl"
    record = asdict(_checkpoint())
    record["sequence"] = sequence
    record["previous_digest"] = previous_digest
    record["digest"] = _record_payload_digest(record)
    _write_chain(path, record)

    with pytest.raises(
        CheckpointIntegrityError, match="genesis|previous_digest|sequence"
    ):
        load_latest_checkpoint(path)


@pytest.mark.parametrize(
    ("field_name", "new_value"),
    [
        ("state_id", "capsule-state-2"),
        ("input_shas", {"remote_main": "9" * 40}),
        ("capsule_root", "8" * 64),
        ("manifest_digest", "7" * 64),
    ],
)
def test_load_rejects_immutable_chain_binding_drift(
    tmp_path: Path,
    field_name: str,
    new_value: object,
) -> None:
    path = tmp_path / f"{field_name}.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first, **{field_name: new_value})

    _write_chain(path, asdict(first), asdict(second))

    with pytest.raises(CheckpointIntegrityError, match=field_name):
        load_latest_checkpoint(path)


def test_append_rejects_stale_sequence_after_intervening_append(tmp_path: Path) -> None:
    path = tmp_path / "stale.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)
    stale = _next_checkpoint(first, phase="stale-follow-up")

    append_checkpoint(path, first)
    append_checkpoint(path, second)
    before = path.read_bytes()

    with pytest.raises(CheckpointIntegrityError, match="sequence|previous_digest"):
        append_checkpoint(path, stale)

    assert path.read_bytes() == before


def test_append_and_load_reject_unsupported_existing_file_types(tmp_path: Path) -> None:
    directory = tmp_path / "as-directory.jsonl"
    directory.mkdir()
    with pytest.raises(CheckpointIntegrityError, match="regular file|directory"):
        append_checkpoint(directory, _checkpoint())
    with pytest.raises(CheckpointIntegrityError, match="regular file|directory"):
        load_latest_checkpoint(directory)

    source = tmp_path / "source.jsonl"
    append_checkpoint(source, _checkpoint())
    hardlink = tmp_path / "hardlink.jsonl"
    _link_or_skip(source, hardlink, symbolic=False)
    with pytest.raises(CheckpointIntegrityError, match="hardlink"):
        load_latest_checkpoint(hardlink)
    with pytest.raises(CheckpointIntegrityError, match="hardlink"):
        append_checkpoint(hardlink, _next_checkpoint(_checkpoint()))


def test_append_and_load_reject_symbolic_aliases_when_supported(tmp_path: Path) -> None:
    real = tmp_path / "real.jsonl"
    append_checkpoint(real, _checkpoint())

    link = tmp_path / "link.jsonl"
    _link_or_skip(real, link, symbolic=True)

    with pytest.raises(CheckpointIntegrityError, match="symlink|reparse|alias"):
        load_latest_checkpoint(link)
    with pytest.raises(CheckpointIntegrityError, match="symlink|reparse|alias"):
        append_checkpoint(link, _next_checkpoint(_checkpoint()))


def test_phase_progression_is_allowed_but_ordered_lists_are_preserved(
    tmp_path: Path,
) -> None:
    path = tmp_path / "progression.jsonl"
    first = _checkpoint(
        completed_actions=("step-b", "step-a"),
        blockers=("blocker-b", "blocker-a"),
        human_decisions=("decision-b", "decision-a"),
    )
    second = _next_checkpoint(
        first,
        phase="containment-ready",
        completed_actions=("step-c", "step-b", "step-a"),
        blockers=("only-one-blocker",),
        human_decisions=("decision-c", "decision-b"),
    )

    append_checkpoint(path, first)
    append_checkpoint(path, second)

    latest = load_latest_checkpoint(path)
    assert latest.phase == "containment-ready"
    assert latest.completed_actions == ("step-c", "step-b", "step-a")
    assert latest.blockers == ("only-one-blocker",)
    assert latest.human_decisions == ("decision-c", "decision-b")


def test_append_completes_reviewer_reported_single_short_write_repro(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    _inject_faulty_fdopen(
        monkeypatch,
        write_actions=[("short", len(canonical_json_bytes(second)) // 3)],
    )

    append_checkpoint(path, second)

    assert path.read_bytes().startswith(committed)
    assert load_latest_checkpoint(path) == second


def test_append_completes_repeated_short_writes_without_corrupting_chain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _verified_checkpoint(first)

    append_checkpoint(path, first)
    _inject_faulty_fdopen(
        monkeypatch,
        write_actions=[("short", 9), ("short", 7), ("short", 5)],
    )

    append_checkpoint(path, second)

    assert load_latest_checkpoint(path) == second


@pytest.mark.parametrize(
    "write_actions",
    [
        [("zero", None)],
        [("raise-after-partial", 11)],
    ],
)
def test_append_failure_modes_restore_the_verified_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    write_actions: list[tuple[str, int | None]],
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    _inject_faulty_fdopen(monkeypatch, write_actions=write_actions)

    with pytest.raises(CheckpointIntegrityError, match="write|progress|partial"):
        append_checkpoint(path, second)

    assert load_latest_checkpoint(path) == first
    assert path.read_bytes() == committed


def test_append_rolls_back_when_flush_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    _inject_faulty_fdopen(monkeypatch, flush_error=OSError("injected flush failure"))

    with pytest.raises(CheckpointIntegrityError, match="flush|write|append"):
        append_checkpoint(path, second)

    assert load_latest_checkpoint(path) == first
    assert path.read_bytes() == committed


def test_append_rolls_back_when_fsync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    calls = {"count": 0}
    original_fsync = checkpoint_module._fsync_descriptor

    def failing_fsync(fd: int) -> None:
        calls["count"] += 1
        if calls["count"] >= 2:
            raise OSError("injected fsync failure")
        original_fsync(fd)

    monkeypatch.setattr(checkpoint_module, "_fsync_descriptor", failing_fsync)

    with pytest.raises(CheckpointIntegrityError, match="fsync|append|write"):
        append_checkpoint(path, second)

    assert load_latest_checkpoint(path) == first
    assert path.read_bytes() == committed


def test_append_rolls_back_when_post_write_verification_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _next_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    calls = {"count": 0}
    original_read = checkpoint_module._read_stream_bytes

    def corrupted_second_read(stream, actual_path: Path) -> bytes:
        calls["count"] += 1
        raw = original_read(stream, actual_path)
        if calls["count"] == 2:
            return raw[:-1]
        return raw

    monkeypatch.setattr(checkpoint_module, "_read_stream_bytes", corrupted_second_read)

    with pytest.raises(CheckpointIntegrityError, match="verification|truncated|append"):
        append_checkpoint(path, second)

    monkeypatch.setattr(checkpoint_module, "_read_stream_bytes", original_read)
    assert load_latest_checkpoint(path) == first
    assert path.read_bytes() == committed


def test_load_repairs_authenticated_trailing_fragment_from_pending_intent(
    tmp_path: Path,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _verified_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    pending_bytes = canonical_json_bytes(second)
    _write_intent(path, committed, second)
    path.write_bytes(committed + pending_bytes[: len(pending_bytes) // 3])

    assert load_latest_checkpoint(path) == first
    assert path.read_bytes() == committed
    assert not _intent_path(path).exists()


def test_load_rejects_unauthenticated_or_interior_corrupt_recovery_cases(
    tmp_path: Path,
) -> None:
    path = tmp_path / "checkpoints.jsonl"
    first = _checkpoint()
    second = _verified_checkpoint(first)

    append_checkpoint(path, first)
    committed = path.read_bytes()
    pending_bytes = canonical_json_bytes(second)
    _write_intent(path, committed, second)
    path.write_bytes(committed[:-1] + b"X" + pending_bytes[: len(pending_bytes) // 3])

    with pytest.raises(CheckpointIntegrityError, match="committed|recovery|prefix"):
        load_latest_checkpoint(path)

    path.write_bytes(committed + b'{"garbage":true}\n')
    with pytest.raises(CheckpointIntegrityError, match="recovery|unauthenticated|tail"):
        load_latest_checkpoint(path)


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("verification_digest", "A" * 64, "verification_digest"),
        ("verification_digest", "a" * 63, "verification_digest"),
        ("verification_digest", "", "verification_digest"),
        ("state_id", "   ", "state_id"),
        ("phase", "\n", "phase"),
        ("next_safe_command", " \t ", "next_safe_command"),
        ("next_safe_command", "echo one\necho two", "next_safe_command"),
        ("recovery_command", "\r", "recovery_command"),
    ],
)
def test_checkpoint_rejects_invalid_verification_and_operator_strings(
    field_name: str,
    value: object,
    match: str,
) -> None:
    data = {
        "schema_version": "1.0.0",
        "sequence": 0,
        "previous_digest": None,
        "state_id": "capsule-state-1",
        "phase": "capture-complete",
        "input_shas": {"remote_main": "1" * 40},
        "capsule_root": "3" * 64,
        "manifest_digest": "4" * 64,
        "verification_digest": None,
        "completed_actions": ("captured-six-planes",),
        "blockers": ("restore-pending",),
        "human_decisions": ("preserve-read-only-first",),
        "next_safe_command": "python -m pytest packages/salvage_spine/tests -q",
        "recovery_command": "python scripts/rebuild_capsule.py --state capsule-state-1",
        "digest": None,
    }
    data[field_name] = value

    with pytest.raises((TypeError, ValueError), match=match):
        Checkpoint(**data)


def test_verification_digest_can_progress_once_and_then_bind(
    tmp_path: Path,
) -> None:
    path = tmp_path / "verification-progress.jsonl"
    first = _checkpoint()
    second = _verified_checkpoint(first)
    third = _next_checkpoint(second, phase="containment-ready")

    _write_chain(path, asdict(first), asdict(second), asdict(third))

    assert load_latest_checkpoint(path) == third
    assert load_latest_checkpoint(path).verification_digest == "5" * 64


@pytest.mark.parametrize(
    ("third_digest", "match"),
    [
        (None, "verification_digest"),
        ("6" * 64, "verification_digest"),
    ],
)
def test_verification_digest_cannot_regress_or_change_once_bound(
    tmp_path: Path,
    third_digest: str | None,
    match: str,
) -> None:
    path = tmp_path / "verification-regress.jsonl"
    first = _checkpoint()
    second = _verified_checkpoint(first)
    third = _next_checkpoint(
        second,
        phase="containment-ready",
        verification_digest=third_digest,
    )

    _write_chain(path, asdict(first), asdict(second), asdict(third))

    with pytest.raises(CheckpointIntegrityError, match=match):
        load_latest_checkpoint(path)
