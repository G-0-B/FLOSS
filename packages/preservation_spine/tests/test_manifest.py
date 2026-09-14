from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from packages.preservation_spine.manifest import (
    inventory_change_universe,
    manifest_digest,
    validate_manifest,
)
from packages.preservation_spine.models import PlaneId, ResultStatus, canonical_json_bytes
from packages.preservation_spine.seal import CapsuleVerificationError, seal_capsule


def _atom(atom_id: str = "atom-a") -> dict[str, object]:
    return {
        "atom_id": atom_id,
        "source_plane": "local-tracked",
        "source_commit": "a" * 64,
        "path_before": "before.txt",
        "path_after": "after.txt",
        "blob_before": "b" * 40,
        "blob_after": "c" * 40,
        "mode_before": "100644",
        "mode_after": "100755",
        "exact_diff_digest": "d" * 64,
    }


def _item(
    item_id: str = "item-a",
    atom_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "item_id": item_id,
        "revision_id": f"revision-{item_id}",
        "atom_ids": atom_ids or ["atom-a"],
        "primary_lane": "preservation-admin",
        "classification_state": "captured",
        "disposition": None,
        "required_gate_ids": [],
        "dependencies": [],
        "blockers": [],
        "required_profiles": [],
        "replacement_item_id": None,
        "notes": "No salvage intent inferred.",
    }


def _manifest() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "state_id": "state-a",
        "capsule_root": "e" * 64,
        "atoms": [_atom()],
        "items": [_item()],
    }


def test_validate_manifest_accepts_exactly_owned_captured_atom() -> None:
    assert validate_manifest(_manifest()) == []


def test_validate_manifest_rejects_orphan_and_multiply_owned_atoms() -> None:
    orphan = _manifest()
    orphan["items"] = []
    assert any("orphan" in error for error in validate_manifest(orphan))

    multiply_owned = _manifest()
    multiply_owned["items"] = [_item("item-a"), _item("item-b")]
    assert any(
        "multiple owners" in error for error in validate_manifest(multiply_owned)
    )


def test_validate_manifest_rejects_missing_atom_reference() -> None:
    data = _manifest()
    data["items"] = [_item(atom_ids=["atom-missing"])]
    assert any("missing atom" in error for error in validate_manifest(data))


def test_validate_manifest_enforces_classification_transition() -> None:
    captured = _manifest()
    captured_item = copy.deepcopy(captured["items"][0])
    captured_item["disposition"] = "salvage"
    captured["items"] = [captured_item]
    assert any(
        "captured" in error and "null disposition" in error
        for error in validate_manifest(captured)
    )

    classified = _manifest()
    classified_item = copy.deepcopy(classified["items"][0])
    classified_item["classification_state"] = "classified"
    classified["items"] = [classified_item]
    assert any(
        "classified" in error and "disposition" in error
        for error in validate_manifest(classified)
    )


def test_validate_manifest_rejects_duplicate_and_ambiguous_atom_ids() -> None:
    duplicate = _manifest()
    duplicate["atoms"] = [_atom(), _atom()]
    assert any("duplicate atom ID" in error for error in validate_manifest(duplicate))

    ambiguous = _manifest()
    ambiguous["atoms"] = [_atom("atom-a"), _atom("atom-b")]
    ambiguous["items"] = [_item("item-a", ["atom-a"]), _item("item-b", ["atom-b"])]
    assert any(
        "ambiguous duplicate atom identity" in error
        for error in validate_manifest(ambiguous)
    )


@pytest.mark.parametrize("dependency_type", ["requires", "generated_by"])
def test_validate_manifest_rejects_dependency_cycles(dependency_type: str) -> None:
    data = _manifest()
    atom_b = _atom("atom-b")
    atom_b["path_after"] = "other.txt"
    item_a = _item("item-a", ["atom-a"])
    item_b = _item("item-b", ["atom-b"])
    item_a["dependencies"] = [{"type": dependency_type, "item": "item-b"}]
    item_b["dependencies"] = [{"type": dependency_type, "item": "item-a"}]
    data["atoms"] = [_atom(), atom_b]
    data["items"] = [item_a, item_b]
    assert any("dependency cycle" in error for error in validate_manifest(data))


def test_validate_manifest_rejects_revise_without_existing_replacement() -> None:
    data = _manifest()
    item = copy.deepcopy(data["items"][0])
    item["classification_state"] = "classified"
    item["disposition"] = "revise"
    item["replacement_item_id"] = "item-missing"
    data["items"] = [item]
    assert any(
        "replacement item is missing" in error for error in validate_manifest(data)
    )


def test_validate_manifest_requires_revision_scoped_gate_for_protected_action() -> None:
    data = _manifest()
    item = copy.deepcopy(data["items"][0])
    item["classification_state"] = "classified"
    item["disposition"] = "salvage"
    item["primary_lane"] = "holochain-integrity"
    item["required_gate_ids"] = ["gate:item-a:wrong-revision:apply"]
    data["items"] = [item]
    errors = validate_manifest(data)
    assert any("not scope-bound" in error for error in errors)

    item["required_gate_ids"] = []
    assert any("required-gate action" in error for error in validate_manifest(data))

    item["required_gate_ids"] = ["gate:item-a:revision-item-a:apply"]
    assert validate_manifest(data) == []


def test_manifest_digest_is_canonical_and_content_sensitive() -> None:
    data = _manifest()
    reordered = {key: data[key] for key in reversed(data)}
    assert manifest_digest(data) == manifest_digest(reordered)
    changed = copy.deepcopy(data)
    changed["atoms"][0]["mode_after"] = "100644"
    assert manifest_digest(data) != manifest_digest(changed)


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "bad\nname.txt",
        "bad\tname.txt",
        "bad\rname.txt",
        "bad\x1bname.txt",
        "bad\x7fname.txt",
        "bad\x85name.txt",
        "bad\u202ename.txt",
        "bad\u2066name.txt",
        "bad\u200bname.txt",
        "bad\u2215name.txt",
        "A\u030a.txt",
    ],
)
def test_validate_manifest_rejects_non_single_line_or_ambiguous_paths(
    unsafe_path: str,
) -> None:
    data = _manifest()
    data["atoms"][0]["path_after"] = unsafe_path
    assert any("path_after is unsafe" in error for error in validate_manifest(data))


def test_validate_manifest_accepts_normalized_printable_non_ascii_paths() -> None:
    data = _manifest()
    data["atoms"][0]["path_before"] = "Ångström/猫.txt"
    data["atoms"][0]["path_after"] = "ångström/猫.txt"
    assert validate_manifest(data) == []


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


def _sealed_capsule(
    tmp_path: Path,
    *,
    staged_diff: bytes = b"",
    unstaged_diff: bytes = b"",
    tracked_manifest: list[dict[str, object]] | None = None,
    untracked_manifest: list[dict[str, object]] | None = None,
    index_metadata_overrides: dict[str, object] | None = None,
    history_identity_overrides: dict[str, object] | None = None,
) -> Path:
    capsule = tmp_path / "capsule"
    capsule.mkdir(parents=True)
    for index, plane in enumerate(
        (PlaneId.REMOTE_MAIN, PlaneId.REMOTE_PR, PlaneId.LOCAL_HISTORY), start=1
    ):
        root = capsule / plane.value
        root.mkdir()
        subject = f"{index:x}" * 40
        bundle_ref = "refs/heads/master"
        (root / "repository.bundle").write_bytes(
            b"# v2 git bundle\n"
            + f"{subject} {bundle_ref}\n\n".encode()
            + f"PACK-{plane.value}".encode()
        )
        (root / "refs.txt").write_text(
            f"{subject} {bundle_ref}\n", encoding="utf-8", newline="\n"
        )
        identity = {
            "bundle_ref": bundle_ref,
            "bundle_scope": "destination-owned-exact-ref",
            "eligibility": "ineligible",
            "object_format": "sha1",
            "plane_id": plane.value,
            "schema_version": "1",
            "sensitivity": "opaque-sensitive",
            "status": "BLOCKED",
            "subject_id": subject,
            "verification": "opaque-preserved",
        }
        identity.update(history_identity_overrides or {})
        _write_json(root / "identity.json", identity)

    index_root = capsule / PlaneId.LOCAL_INDEX.value
    index_root.mkdir()
    index_bytes = b"exact index bytes"
    (index_root / "index.raw").write_bytes(index_bytes)
    (index_root / "staged.diff").write_bytes(staged_diff)
    index_metadata = {
        "eligibility": "ineligible",
        "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
        "secret_path_exclusions": [],
        "sensitivity": "opaque-sensitive",
        "status": "BLOCKED",
        "verification": "opaque-preserved",
    }
    index_metadata.update(index_metadata_overrides or {})
    _write_json(index_root / "metadata.json", index_metadata)

    def disposition(entries: list[dict[str, object]]) -> dict[str, object]:
        redacted = sorted(
            str(entry["path"])
            for entry in entries
            if entry.get("inclusion") == "redacted"
        )
        if redacted:
            return {
                "eligibility": "ineligible",
                "secret_path_exclusions": redacted,
                "sensitivity": "redacted",
                "status": "BLOCKED",
                "verification": "unverifiable-redacted",
            }
        return {
            "eligibility": "eligible",
            "secret_path_exclusions": [],
            "sensitivity": "ordinary",
            "status": "PASS",
            "verification": "byte-equality",
        }

    tracked_root = capsule / PlaneId.LOCAL_TRACKED.value
    tracked_root.mkdir()
    (tracked_root / "unstaged.diff").write_bytes(unstaged_diff)
    stored_tracked = copy.deepcopy(tracked_manifest or [])
    _write_json(tracked_root / "manifest.json", stored_tracked)
    _write_json(tracked_root / "metadata.json", disposition(stored_tracked))

    untracked_root = capsule / PlaneId.LOCAL_UNTRACKED.value
    untracked_root.mkdir()
    stored_untracked = copy.deepcopy(untracked_manifest or [])
    for entry in stored_untracked:
        if entry.get("inclusion") == "copied":
            payload = untracked_root / "payload" / str(entry["path"])
            payload.parent.mkdir(parents=True, exist_ok=True)
            payload.write_bytes(bytes(entry["content"]))
            del entry["content"]
    _write_json(untracked_root / "metadata.json", disposition(stored_untracked))
    _write_json(untracked_root / "manifest.json", stored_untracked)
    seal_capsule(capsule)
    return capsule


def test_inventory_is_deterministic_complete_and_defaults_to_captured(
    tmp_path: Path,
) -> None:
    payload = b"untracked bytes\n"
    capsule = _sealed_capsule(
        tmp_path,
        tracked_manifest=[
            {
                "path": "tracked.txt",
                "kind": "file",
                "mode": 0o644,
                "size": 4,
                "sha256": hashlib.sha256(b"data").hexdigest(),
                "inclusion": "metadata-only",
                "reason": "tracked-worktree-inventory",
            }
        ],
        untracked_manifest=[
            {
                "path": "new.txt",
                "kind": "file",
                "mode": 0o644,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "inclusion": "copied",
                "reason": "untracked",
                "content": payload,
            }
        ],
    )
    first = inventory_change_universe(capsule)
    second = inventory_change_universe(capsule)
    assert first == second
    schema_path = (
        Path(__file__).parents[3]
        / "docs"
        / "superpowers"
        / "specs"
        / "preservation-manifest.schema.json"
    )
    Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8"))).validate(
        first
    )
    assert validate_manifest(first) == []
    assert len(first["atoms"]) == len(first["items"])
    assert all(item["classification_state"] == "captured" for item in first["items"])
    assert all(item["disposition"] is None for item in first["items"])
    assert [atom["atom_id"] for atom in first["atoms"]] == sorted(
        atom["atom_id"] for atom in first["atoms"]
    )
    serialized = json.dumps(first)
    assert str(capsule.resolve()) not in serialized


def test_inventory_preserves_case_only_rename_and_mode_blob_identity(
    tmp_path: Path,
) -> None:
    old_blob = "a" * 40
    new_blob = "b" * 40
    diff = (
        b"diff --git a/Foo.txt b/foo.txt\n"
        b"similarity index 100%\n"
        b"rename from Foo.txt\n"
        b"rename to foo.txt\n"
        b"diff --git a/tool.sh b/tool.sh\n"
        b"old mode 100644\n"
        b"new mode 100755\n"
        + f"diff --git a/data.bin b/data.bin\nindex {old_blob}..{new_blob} 100644\n".encode()
        + b"--- a/data.bin\n+++ b/data.bin\n@@ -1 +1 @@\n-old\n+new\n"
    )
    manifest = inventory_change_universe(_sealed_capsule(tmp_path, staged_diff=diff))
    atoms = manifest["atoms"]
    rename = next(
        atom
        for atom in atoms
        if atom["path_before"] == "Foo.txt" and atom["path_after"] == "foo.txt"
    )
    assert rename["path_before"] != rename["path_after"]
    mode = next(atom for atom in atoms if atom["path_after"] == "tool.sh")
    assert (mode["mode_before"], mode["mode_after"]) == ("100644", "100755")
    blob = next(atom for atom in atoms if atom["path_after"] == "data.bin")
    assert (blob["blob_before"], blob["blob_after"]) == (old_blob, new_blob)
    assert len({rename["atom_id"], mode["atom_id"], blob["atom_id"]}) == 3


def test_inventory_decodes_git_octal_quoted_utf8_path(tmp_path: Path) -> None:
    diff = (
        rb'diff --git "a/\303\205.txt" "b/\303\245.txt"'
        + b"\n"
        + rb'rename from "\303\205.txt"'
        + b"\n"
        + rb'rename to "\303\245.txt"'
        + b"\n"
    )
    data = inventory_change_universe(_sealed_capsule(tmp_path, staged_diff=diff))
    atom = next(atom for atom in data["atoms"] if atom["path_before"] == "Å.txt")
    assert atom["path_after"] == "å.txt"


@pytest.mark.parametrize(
    "quoted_path",
    [
        rb"bad\nname.txt",
        rb"bad\tname.txt",
        rb"bad\rname.txt",
        rb"bad\033name.txt",
        rb"bad\177name.txt",
        rb"bad\302\205name.txt",
        rb"bad\342\200\256name.txt",
        rb"bad\342\201\246name.txt",
    ],
)
def test_inventory_rejects_quoted_git_control_and_format_paths(
    tmp_path: Path,
    quoted_path: bytes,
) -> None:
    diff = (
        b'diff --git "a/'
        + quoted_path
        + b'" "b/'
        + quoted_path
        + b'"\nnew file mode 100644\n--- /dev/null\n+++ "b/'
        + quoted_path
        + b'"\n@@ -0,0 +1 @@\n+x\n'
    )
    with pytest.raises(CapsuleVerificationError, match="unsafe"):
        inventory_change_universe(_sealed_capsule(tmp_path, staged_diff=diff))


def test_inventory_rejects_out_of_range_octal_escape(tmp_path: Path) -> None:
    """Git escapes single bytes (\\000–\\377).  A tampered capsule with
    \\400 or higher must raise CapsuleVerificationError — not the bare
    ValueError from bytearray.append, which escapes the capsule error
    contract callers rely on."""
    diff = (
        b'diff --git "a/\\400.txt" "b/\\400.txt"\n'
        + b'new file mode 100644\n--- /dev/null\n+++ "b/\\400.txt"\n@@ -0,0 +1 @@\n+x\n'
    )
    with pytest.raises(CapsuleVerificationError):
        inventory_change_universe(_sealed_capsule(tmp_path, staged_diff=diff))


def test_inventory_rejects_tamper_and_unsafe_manifest_path(tmp_path: Path) -> None:
    capsule = _sealed_capsule(tmp_path)
    (capsule / PlaneId.LOCAL_INDEX.value / "index.raw").write_bytes(b"tampered")
    with pytest.raises(CapsuleVerificationError):
        inventory_change_universe(capsule)

    unsafe_root = tmp_path / "unsafe"
    unsafe_root.mkdir()
    unsafe = _sealed_capsule(
        unsafe_root,
        untracked_manifest=[
            {
                "path": "../escape.txt",
                "kind": "redacted",
                "mode": None,
                "size": None,
                "sha256": None,
                "inclusion": "redacted",
                "reason": "secret-name",
            }
        ],
    )
    with pytest.raises(CapsuleVerificationError, match="unsafe"):
        inventory_change_universe(unsafe)


def test_inventory_accepts_real_capture_and_seal(tmp_path: Path) -> None:
    from packages.preservation_spine.tests.test_seal_restore import captured_capsule

    capsule, _, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    data = inventory_change_universe(capsule)
    assert validate_manifest(data) == []
    assert {atom["source_plane"] for atom in data["atoms"]} == {
        plane.value for plane in PlaneId
    }
    regular = next(
        atom
        for atom in data["atoms"]
        if atom["source_plane"] == PlaneId.LOCAL_TRACKED.value
        and atom["path_after"] == "local.txt"
        and atom["blob_after"] is not None
    )
    assert regular["mode_after"] == "100644"


def test_inventory_rejects_sealed_payload_metadata_disagreement(tmp_path: Path) -> None:
    payload = b"actual"
    capsule = _sealed_capsule(
        tmp_path,
        untracked_manifest=[
            {
                "path": "payload.txt",
                "kind": "file",
                "mode": 0o644,
                "size": len(payload) + 1,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "inclusion": "copied",
                "reason": "untracked",
                "content": payload,
            }
        ],
    )
    with pytest.raises(CapsuleVerificationError, match="payload disagrees"):
        inventory_change_universe(capsule)


@pytest.mark.parametrize(
    ("plane", "entry", "expected_blocker"),
    [
        (
            PlaneId.LOCAL_TRACKED,
            {
                "path": "tracked.txt",
                "kind": "file",
                "mode": 0o644,
                "size": 4,
                "sha256": hashlib.sha256(b"data").hexdigest(),
                "inclusion": "metadata-only",
                "reason": "tracked-worktree-inventory",
            },
            None,
        ),
        (
            PlaneId.LOCAL_UNTRACKED,
            {
                "path": "copied.txt",
                "kind": "file",
                "mode": 0o644,
                "size": 4,
                "sha256": hashlib.sha256(b"data").hexdigest(),
                "inclusion": "copied",
                "reason": "untracked",
                "content": b"data",
            },
            None,
        ),
        (
            PlaneId.LOCAL_TRACKED,
            {
                "path": ".env",
                "kind": "redacted",
                "mode": None,
                "size": None,
                "sha256": None,
                "inclusion": "redacted",
                "reason": "secret-name",
            },
            "redacted-evidence-ineligible",
        ),
        (
            PlaneId.LOCAL_UNTRACKED,
            {
                "path": ".secret",
                "kind": "redacted",
                "mode": None,
                "size": None,
                "sha256": None,
                "inclusion": "redacted",
                "reason": "secret-name",
            },
            "redacted-evidence-ineligible",
        ),
        (
            PlaneId.LOCAL_TRACKED,
            {
                "path": "missing.txt",
                "kind": "missing",
                "mode": None,
                "size": None,
                "sha256": None,
                "inclusion": "excluded",
                "reason": "missing-from-worktree",
            },
            "excluded-evidence-ineligible",
        ),
        (
            PlaneId.LOCAL_UNTRACKED,
            {
                "path": "special-dir",
                "kind": "directory",
                "mode": 0o755,
                "size": None,
                "sha256": None,
                "inclusion": "excluded",
                "reason": "special-file-not-copied",
            },
            "excluded-evidence-ineligible",
        ),
    ],
)
def test_inventory_and_task4_accept_the_same_inclusion_states(
    tmp_path: Path,
    plane: PlaneId,
    entry: dict[str, object],
    expected_blocker: str | None,
) -> None:
    from packages.preservation_spine.restore import _validate_artifact_plane

    kwargs = (
        {"tracked_manifest": [entry]}
        if plane is PlaneId.LOCAL_TRACKED
        else {"untracked_manifest": [entry]}
    )
    capsule = _sealed_capsule(tmp_path, **kwargs)
    data = inventory_change_universe(capsule)
    task4_result = _validate_artifact_plane(capsule, plane)
    atom = next(
        atom
        for atom in data["atoms"]
        if atom["source_plane"] == plane.value and atom["path_after"] == entry["path"]
    )
    item = next(item for item in data["items"] if atom["atom_id"] in item["atom_ids"])
    if expected_blocker is None:
        assert task4_result.status is ResultStatus.PASS
        assert item["blockers"] == []
    else:
        assert task4_result.status is ResultStatus.BLOCKED
        assert expected_blocker in task4_result.blockers
        assert item["blockers"] == [expected_blocker]
    assert item["classification_state"] == "captured"
    assert item["disposition"] is None


@pytest.mark.parametrize(
    ("plane", "entry"),
    [
        (
            PlaneId.LOCAL_TRACKED,
            {
                "path": "tracked.txt",
                "kind": "file",
                "mode": 0o644,
                "size": 4,
                "sha256": hashlib.sha256(b"data").hexdigest(),
                "inclusion": "eligible",
                "reason": "content-read",
            },
        ),
        (
            PlaneId.LOCAL_TRACKED,
            {
                "path": "tracked.txt",
                "kind": "file",
                "mode": 0o644,
                "size": 4,
                "sha256": hashlib.sha256(b"data").hexdigest(),
                "inclusion": "metadata-only",
                "reason": "reason-drift",
            },
        ),
        (
            PlaneId.LOCAL_UNTRACKED,
            {
                "path": "copied.txt",
                "kind": "file",
                "mode": 0o644,
                "size": 4,
                "sha256": hashlib.sha256(b"data").hexdigest(),
                "inclusion": "copied",
                "reason": "reason-drift",
                "content": b"data",
            },
        ),
        (
            PlaneId.LOCAL_UNTRACKED,
            {
                "path": ".env",
                "kind": "redacted",
                "mode": None,
                "size": None,
                "sha256": None,
                "inclusion": "redacted",
                "reason": "reason-drift",
            },
        ),
        (
            PlaneId.LOCAL_UNTRACKED,
            {
                "path": "special-dir",
                "kind": "file",
                "mode": 0o755,
                "size": None,
                "sha256": None,
                "inclusion": "excluded",
                "reason": "special-file-not-copied",
            },
        ),
    ],
)
def test_inventory_and_task4_both_reject_unsupported_inclusion_semantics(
    tmp_path: Path,
    plane: PlaneId,
    entry: dict[str, object],
) -> None:
    from packages.preservation_spine.restore import _validate_artifact_plane

    kwargs = (
        {"tracked_manifest": [entry]}
        if plane is PlaneId.LOCAL_TRACKED
        else {"untracked_manifest": [entry]}
    )
    capsule = _sealed_capsule(tmp_path, **kwargs)
    with pytest.raises(CapsuleVerificationError):
        inventory_change_universe(capsule)
    with pytest.raises(CapsuleVerificationError):
        _validate_artifact_plane(capsule, plane)


def test_inventory_rejects_index_and_history_disposition_drift(tmp_path: Path) -> None:
    index_capsule = _sealed_capsule(
        tmp_path / "index",
        index_metadata_overrides={"eligibility": "eligible"},
    )
    with pytest.raises(CapsuleVerificationError):
        inventory_change_universe(index_capsule)

    history_capsule = _sealed_capsule(
        tmp_path / "history",
        history_identity_overrides={"status": "PASS"},
    )
    with pytest.raises(CapsuleVerificationError):
        inventory_change_universe(history_capsule)
