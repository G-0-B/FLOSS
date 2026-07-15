from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from packages.salvage_spine.manifest import (
    inventory_change_universe,
    manifest_digest,
    validate_manifest,
)
from packages.salvage_spine.models import PlaneId, canonical_json_bytes
from packages.salvage_spine.seal import CapsuleVerificationError, seal_capsule


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


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


def _sealed_capsule(
    tmp_path: Path,
    *,
    staged_diff: bytes = b"",
    unstaged_diff: bytes = b"",
    tracked_manifest: list[dict[str, object]] | None = None,
    untracked_manifest: list[dict[str, object]] | None = None,
) -> Path:
    capsule = tmp_path / "capsule"
    capsule.mkdir()
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
        _write_json(
            root / "identity.json",
            {
                "bundle_ref": bundle_ref,
                "bundle_scope": "destination-owned-exact-ref",
                "object_format": "sha1",
                "plane_id": plane.value,
                "schema_version": "1",
                "subject_id": subject,
            },
        )

    index_root = capsule / PlaneId.LOCAL_INDEX.value
    index_root.mkdir()
    index_bytes = b"exact index bytes"
    (index_root / "index.raw").write_bytes(index_bytes)
    (index_root / "staged.diff").write_bytes(staged_diff)
    _write_json(
        index_root / "metadata.json",
        {
            "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
            "secret_path_exclusions": [],
        },
    )

    tracked_root = capsule / PlaneId.LOCAL_TRACKED.value
    tracked_root.mkdir()
    (tracked_root / "unstaged.diff").write_bytes(unstaged_diff)
    _write_json(tracked_root / "manifest.json", tracked_manifest or [])
    _write_json(tracked_root / "metadata.json", {"secret_path_exclusions": []})

    untracked_root = capsule / PlaneId.LOCAL_UNTRACKED.value
    untracked_root.mkdir()
    _write_json(untracked_root / "metadata.json", {"secret_path_exclusions": []})
    stored_untracked = copy.deepcopy(untracked_manifest or [])
    for entry in stored_untracked:
        if entry.get("inclusion") == "copied":
            payload = untracked_root / "payload" / str(entry["path"])
            payload.parent.mkdir(parents=True, exist_ok=True)
            payload.write_bytes(bytes(entry["content"]))
            del entry["content"]
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
                "mode": 0o100644,
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
                "mode": 0o100644,
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
        / "pr38-salvage-manifest.schema.json"
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
    from packages.salvage_spine.tests.test_seal_restore import captured_capsule

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
                "mode": 0o100644,
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
