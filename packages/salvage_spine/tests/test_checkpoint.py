from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import os
from pathlib import Path

import pytest

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
            "verification": "2" * 64,
        },
        "capsule_root": "3" * 64,
        "manifest_digest": "4" * 64,
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

    assert path.read_bytes() == canonical_json_bytes(first) + canonical_json_bytes(second)
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

    with pytest.raises(CheckpointIntegrityError, match="genesis|previous_digest|sequence"):
        load_latest_checkpoint(path)


@pytest.mark.parametrize(
    ("field_name", "new_value"),
    [
        ("state_id", "capsule-state-2"),
        ("input_shas", {"remote_main": "9" * 40, "verification": "2" * 64}),
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
