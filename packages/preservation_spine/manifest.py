"""Deterministic change-universe inventory and semantic validation.

Capsule evidence remains local, untrusted evidence.  This module inventories it;
it does not authorize projection, infer salvage intent, or establish truth.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from pathlib import PurePosixPath
from pathlib import PureWindowsPath
from typing import Any

from .models import PlaneId, canonical_json_bytes
from .seal import (
    CapsuleVerificationError,
    _capsule_root,
    _read_regular_bytes,
    provenance_root,
)

_HEX_40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
_MODE = re.compile(r"[0-7]{6}\Z")
_DISPOSITIONS = {"salvage", "revise", "park", "reject"}
_DEPENDENCY_TYPES = {"requires", "generated_by", "conflicts_with", "supersedes"}
_ACYCLIC_DEPENDENCIES = {"requires", "generated_by"}
_PROTECTED_LANES = {"holochain-integrity", "consensus-gateway"}
_OPAQUE_DISPOSITION = (
    "opaque-sensitive",
    "ineligible",
    "opaque-preserved",
    "BLOCKED",
)
_ORDINARY_DISPOSITION = ("ordinary", "eligible", "byte-equality", "PASS")
_REDACTED_DISPOSITION = (
    "redacted",
    "ineligible",
    "unverifiable-redacted",
    "BLOCKED",
)
_MANIFEST_ENTRY_FIELDS = {
    "inclusion",
    "kind",
    "mode",
    "path",
    "reason",
    "sha256",
    "size",
}
_EXCLUDED_KINDS = {
    "gitlink-not-followed": frozenset({"gitlink"}),
    "missing-from-worktree": frozenset({"missing"}),
    "outside-source-not-followed": frozenset({"file"}),
    "special-file-not-copied": frozenset({"directory", "special"}),
    "symlink-not-followed": frozenset({"symlink"}),
    "symlink-parent-not-followed": frozenset({"file"}),
}
_AMBIGUOUS_PATH_CHARACTERS = frozenset(
    {
        "\u2024",  # one dot leader
        "\u2044",  # fraction slash
        "\u2215",  # division slash
        "\u29f5",  # reverse solidus operator
        "\u29f8",  # big solidus
        "\ufe52",  # small full stop
        "\ufe68",  # small reverse solidus
        "\uff0e",  # fullwidth full stop
        "\uff0f",  # fullwidth solidus
        "\uff3c",  # fullwidth reverse solidus
    }
)
_ATOM_FIELDS = {
    "atom_id",
    "source_plane",
    "source_commit",
    "path_before",
    "path_after",
    "blob_before",
    "blob_after",
    "mode_before",
    "mode_after",
    "exact_diff_digest",
}
_ITEM_FIELDS = {
    "item_id",
    "revision_id",
    "atom_ids",
    "primary_lane",
    "classification_state",
    "disposition",
    "required_gate_ids",
    "dependencies",
    "blockers",
    "required_profiles",
    "replacement_item_id",
    "notes",
}
_TOP_FIELDS = {"schema_version", "state_id", "capsule_root", "atoms", "items"}


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def _cycle_nodes(graph: dict[str, set[str]]) -> set[str]:
    """Return nodes participating in a directed cycle."""

    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cyclic: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            start = stack.index(node)
            cyclic.update(stack[start:])
            return
        visiting.add(node)
        stack.append(node)
        for target in sorted(graph.get(node, set())):
            visit(target)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)
    return cyclic


def _validate_atom(atom: object, index: int, errors: list[str]) -> str | None:
    label = f"atoms[{index}]"
    if not isinstance(atom, dict):
        errors.append(f"{label} must be an object")
        return None
    keys = set(atom)
    if keys != _ATOM_FIELDS:
        errors.append(f"{label} fields must exactly match the atom contract")
    atom_id = atom.get("atom_id")
    if not _nonempty_string(atom_id):
        errors.append(f"{label}.atom_id must be a non-empty string")
        atom_id = None
    if atom.get("source_plane") not in {plane.value for plane in PlaneId}:
        errors.append(f"{label}.source_plane is invalid")
    source_commit = atom.get("source_commit")
    if source_commit is not None and (
        not isinstance(source_commit, str) or not _HEX_40_OR_64.fullmatch(source_commit)
    ):
        errors.append(f"{label}.source_commit must be null or lowercase hex")
    for field in ("path_before", "path_after"):
        value = atom.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"{label}.{field} must be null or a string")
        elif isinstance(value, str) and not _is_safe_manifest_path(value):
            errors.append(f"{label}.{field} is unsafe")
    for field in ("blob_before", "blob_after"):
        value = atom.get(field)
        if value is not None and (
            not isinstance(value, str) or not _HEX_40_OR_64.fullmatch(value)
        ):
            errors.append(f"{label}.{field} must be null or lowercase hex")
    for field in ("mode_before", "mode_after"):
        value = atom.get(field)
        if value is not None and (
            not isinstance(value, str) or not _MODE.fullmatch(value)
        ):
            errors.append(f"{label}.{field} must be null or a six-digit octal mode")
    exact_diff_digest = atom.get("exact_diff_digest")
    if not isinstance(exact_diff_digest, str) or not _HEX_64.fullmatch(
        exact_diff_digest
    ):
        errors.append(f"{label}.exact_diff_digest must be lowercase SHA-256")
    return atom_id if isinstance(atom_id, str) else None


def validate_manifest(data: dict) -> list[str]:
    """Return deterministic semantic and structural errors for a manifest.

    A gate ID is scope-bound only in the form
    ``gate:<item_id>:<revision_id>:<non-empty-scope>``.
    """

    errors: list[str] = []
    if not isinstance(data, dict):
        return ["manifest must be an object"]
    if set(data) != _TOP_FIELDS:
        errors.append("top-level fields must exactly match the manifest contract")
    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if not _nonempty_string(data.get("state_id")):
        errors.append("state_id must be a non-empty string")
    capsule_root = data.get("capsule_root")
    if not isinstance(capsule_root, str) or not _HEX_64.fullmatch(capsule_root):
        errors.append("capsule_root must be lowercase SHA-256")

    raw_atoms = data.get("atoms")
    if not isinstance(raw_atoms, list):
        errors.append("atoms must be an array")
        raw_atoms = []
    atom_ids = [
        atom_id
        for index, atom in enumerate(raw_atoms)
        if (atom_id := _validate_atom(atom, index, errors)) is not None
    ]
    for atom_id in _duplicates(atom_ids):
        errors.append(f"duplicate atom ID: {atom_id}")
    # Membership set alongside the list. The list is still needed for duplicate
    # detection, but every atom reference on every item was tested against it
    # with `in` -- a linear scan. `inventory_change_universe` creates one atom
    # and one item per capsule entry, so validation cost grew as O(N^2) in the
    # number of atoms and dominated `inventory` on large untracked or tracked
    # planes.
    atom_id_set = set(atom_ids)

    identity_owners: dict[bytes, list[str]] = defaultdict(list)
    for atom in raw_atoms:
        if isinstance(atom, dict) and _nonempty_string(atom.get("atom_id")):
            identity = {
                key: atom.get(key) for key in sorted(_ATOM_FIELDS - {"atom_id"})
            }
            identity_owners[canonical_json_bytes(identity)].append(str(atom["atom_id"]))
    for owners in identity_owners.values():
        if len(set(owners)) > 1:
            errors.append(
                "ambiguous duplicate atom identity: " + ", ".join(sorted(set(owners)))
            )

    raw_items = data.get("items")
    if not isinstance(raw_items, list):
        errors.append("items must be an array")
        raw_items = []
    item_ids: list[str] = []
    owned_by: dict[str, list[str]] = defaultdict(list)
    graph: dict[str, set[str]] = defaultdict(set)
    pending_replacements: list[tuple[str, object]] = []

    for index, item in enumerate(raw_items):
        label = f"items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(item) != _ITEM_FIELDS:
            errors.append(f"{label} fields must exactly match the item contract")
        item_id = item.get("item_id")
        revision_id = item.get("revision_id")
        if not _nonempty_string(item_id):
            errors.append(f"{label}.item_id must be a non-empty string")
            item_id = f"<invalid-{index}>"
        else:
            item_ids.append(item_id)
        if not _nonempty_string(revision_id):
            errors.append(f"{label}.revision_id must be a non-empty string")
        if not _nonempty_string(item.get("primary_lane")):
            errors.append(f"{label}.primary_lane must be a non-empty string")

        refs = item.get("atom_ids")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label}.atom_ids must be a non-empty array")
            refs = []
        valid_refs = [ref for ref in refs if _nonempty_string(ref)]
        if len(valid_refs) != len(refs):
            errors.append(f"{label}.atom_ids contains a malformed reference")
        for ref in _duplicates(valid_refs):
            errors.append(f"{label}.atom_ids repeats atom: {ref}")
        for ref in valid_refs:
            if ref not in atom_id_set:
                errors.append(f"{label} references missing atom: {ref}")
            owned_by[ref].append(str(item_id))

        state = item.get("classification_state")
        disposition = item.get("disposition")
        replacement = item.get("replacement_item_id")
        if state == "captured":
            if disposition is not None:
                errors.append(f"{label} captured item must have null disposition")
        elif state == "classified":
            if disposition not in _DISPOSITIONS:
                errors.append(f"{label} classified item requires a valid disposition")
        else:
            errors.append(f"{label}.classification_state is invalid")
        if disposition == "revise":
            if not _nonempty_string(replacement):
                errors.append(f"{label} revise disposition requires a replacement")
            else:
                pending_replacements.append((str(item_id), replacement))
        elif replacement is not None:
            errors.append(f"{label} replacement is only valid for revise disposition")

        gates = item.get("required_gate_ids")
        if not isinstance(gates, list):
            errors.append(f"{label}.required_gate_ids must be an array")
            gates = []
        valid_gates = [gate for gate in gates if _nonempty_string(gate)]
        if len(valid_gates) != len(gates):
            errors.append(f"{label}.required_gate_ids contains a malformed gate ID")
        for gate in _duplicates(valid_gates):
            errors.append(f"{label}.required_gate_ids repeats gate: {gate}")
        gate_prefix = f"gate:{item_id}:{revision_id}:"
        for gate in valid_gates:
            if not gate.startswith(gate_prefix) or gate == gate_prefix:
                errors.append(
                    f"{label} gate ID is not scope-bound to item revision: {gate}"
                )
        if (
            item.get("primary_lane") in _PROTECTED_LANES
            and state == "classified"
            and disposition in {"salvage", "revise"}
            and not valid_gates
        ):
            errors.append(f"{label} required-gate action lacks a scope-bound gate ID")

        dependencies = item.get("dependencies")
        if not isinstance(dependencies, list):
            errors.append(f"{label}.dependencies must be an array")
            dependencies = []
        for dep_index, dependency in enumerate(dependencies):
            dep_label = f"{label}.dependencies[{dep_index}]"
            if not isinstance(dependency, dict) or set(dependency) != {"type", "item"}:
                errors.append(f"{dep_label} is malformed")
                continue
            dep_type = dependency.get("type")
            target = dependency.get("item")
            if dep_type not in _DEPENDENCY_TYPES or not _nonempty_string(target):
                errors.append(f"{dep_label} is malformed")
                continue
            if dep_type in _ACYCLIC_DEPENDENCIES:
                graph[str(item_id)].add(target)

        for field in ("blockers", "required_profiles"):
            values = item.get(field)
            if not isinstance(values, list) or not all(
                isinstance(value, str) and (field == "blockers" or bool(value))
                for value in values
            ):
                errors.append(f"{label}.{field} is malformed")
            elif field == "required_profiles":
                for value in _duplicates(values):
                    errors.append(f"{label}.required_profiles repeats profile: {value}")
        if not isinstance(item.get("notes"), str):
            errors.append(f"{label}.notes must be a string")

    known_items = set(item_ids)
    for item_id in _duplicates(item_ids):
        errors.append(f"duplicate item ID: {item_id}")
    for atom_id in sorted(set(atom_ids)):
        owners = owned_by.get(atom_id, [])
        if not owners:
            errors.append(f"orphan atom has no owner: {atom_id}")
        elif len(owners) > 1:
            errors.append(f"atom has multiple owners: {atom_id}")
    for item_id, replacement in pending_replacements:
        if replacement == item_id:
            errors.append(f"revise replacement cannot reference itself: {item_id}")
        elif replacement not in known_items:
            errors.append(f"revise replacement item is missing: {replacement}")
    for source, targets in graph.items():
        for target in targets:
            if target not in known_items:
                errors.append(f"{source} dependency references missing item: {target}")
    cyclic = _cycle_nodes(graph)
    if cyclic:
        errors.append(
            "requires/generated_by dependency cycle: " + ", ".join(sorted(cyclic))
        )
    return sorted(set(errors))


def manifest_digest(data: dict) -> str:
    """Return the deterministic SHA-256 digest of canonical manifest JSON."""

    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class _VerifiedCapsuleReader:
    """Read only files bound to one authenticated checksum listing."""

    def __init__(self, root: Path):
        self.root = _capsule_root(root)
        self.provenance_root = provenance_root(self.root)
        listing = _read_regular_bytes(self.root / "checksums.sha256")
        if _sha256(listing) != self.provenance_root:
            raise CapsuleVerificationError(
                "checksum listing changed after verification"
            )
        self.expected: dict[str, str] = {}
        for raw_line in listing.splitlines(keepends=True):
            try:
                entry = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CapsuleVerificationError("checksum listing is malformed") from exc
            if (
                not isinstance(entry, dict)
                or set(entry) != {"path", "sha256"}
                or raw_line != canonical_json_bytes(entry)
            ):
                raise CapsuleVerificationError("checksum entry is malformed")
            relative = entry["path"]
            digest = entry["sha256"]
            if (
                not isinstance(relative, str)
                or not _is_safe_manifest_path(relative)
                or not isinstance(digest, str)
                or not _HEX_64.fullmatch(digest)
                or relative in self.expected
            ):
                raise CapsuleVerificationError("checksum entry is unsafe or ambiguous")
            self.expected[relative] = digest

    def read(self, path: Path) -> bytes:
        try:
            relative = path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise CapsuleVerificationError("capsule read escaped its root") from exc
        expected = self.expected.get(relative)
        if expected is None:
            raise CapsuleVerificationError("capsule file is not checksum-authenticated")
        content = _read_regular_bytes(path)
        if _sha256(content) != expected:
            raise CapsuleVerificationError("capsule file changed after verification")
        return content


def _read_json(reader: _VerifiedCapsuleReader, path: Path) -> Any:
    content = reader.read(path)
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleVerificationError("capsule metadata is malformed") from exc
    if content != canonical_json_bytes(value):
        raise CapsuleVerificationError("capsule metadata is not canonical JSON")
    return value


def _is_safe_manifest_path(value: str) -> bool:
    """Require portable, printable, single-line NFC repository paths."""

    if (
        not value
        or "\\" in value
        or not value.isprintable()
        or unicodedata.normalize("NFC", value) != value
        or any(character in _AMBIGUOUS_PATH_CHARACTERS for character in value)
    ):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    pure = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if any(part.endswith((".", " ")) for part in pure.parts):
        return False
    return not (
        pure.is_absolute()
        or ".." in pure.parts
        or value != pure.as_posix()
        or windows.is_absolute()
        or bool(windows.drive)
    )


def _safe_manifest_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise CapsuleVerificationError("manifest path must be a non-empty string")
    if not _is_safe_manifest_path(value):
        raise CapsuleVerificationError("manifest path is unsafe")
    return value


def _mode(value: object, kind: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CapsuleVerificationError("manifest mode is malformed")
    if kind == "file" and value <= 0o7777:
        value = 0o100755 if value & 0o111 else 0o100644
    elif kind == "symlink" and value <= 0o7777:
        value = 0o120000
    rendered = f"{value:06o}"
    if not _MODE.fullmatch(rendered):
        raise CapsuleVerificationError("manifest mode is outside the supported range")
    return rendered


def _optional_digest(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _HEX_40_OR_64.fullmatch(value):
        raise CapsuleVerificationError("manifest content digest is malformed")
    return value


def _atom_id(atom: dict[str, object]) -> str:
    identity = {key: atom[key] for key in sorted(_ATOM_FIELDS - {"atom_id"})}
    return "atom-" + _sha256(canonical_json_bytes(identity))


def _new_atom(
    *,
    source_plane: PlaneId,
    source_commit: str | None,
    path_before: str | None,
    path_after: str | None,
    blob_before: str | None,
    blob_after: str | None,
    mode_before: str | None,
    mode_after: str | None,
    exact_diff_digest: str,
) -> dict[str, object]:
    atom: dict[str, object] = {
        "atom_id": "",
        "source_plane": source_plane.value,
        "source_commit": source_commit,
        "path_before": path_before,
        "path_after": path_after,
        "blob_before": blob_before,
        "blob_after": blob_after,
        "mode_before": mode_before,
        "mode_after": mode_after,
        "exact_diff_digest": exact_diff_digest,
    }
    atom["atom_id"] = _atom_id(atom)
    return atom


def _decode_git_path(value: bytes) -> str:
    encoded = value
    if value.startswith(b'"'):
        if len(value) < 2 or not value.endswith(b'"'):
            raise CapsuleVerificationError("quoted diff path is malformed")
        encoded = bytearray()
        index = 1
        escapes = {
            ord("a"): 7,
            ord("b"): 8,
            ord("t"): 9,
            ord("n"): 10,
            ord("v"): 11,
            ord("f"): 12,
            ord("r"): 13,
            ord('"'): ord('"'),
            ord("\\"): ord("\\"),
        }
        while index < len(value) - 1:
            current = value[index]
            if current != ord("\\"):
                encoded.append(current)
                index += 1
                continue
            index += 1
            if index >= len(value) - 1:
                raise CapsuleVerificationError("quoted diff path is malformed")
            escaped = value[index]
            if ord("0") <= escaped <= ord("7"):
                digits = bytearray()
                for _ in range(3):
                    if index < len(value) - 1 and ord("0") <= value[index] <= ord("7"):
                        digits.append(value[index])
                        index += 1
                    else:
                        break
                encoded.append(int(digits.decode("ascii"), 8))
                continue
            if escaped not in escapes:
                raise CapsuleVerificationError("quoted diff path escape is malformed")
            encoded.append(escapes[escaped])
            index += 1
    try:
        return bytes(encoded).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CapsuleVerificationError("diff path is not valid UTF-8") from exc


def _split_diff_header(line: bytes) -> tuple[str, str]:
    prefix = b"diff --git "
    if not line.startswith(prefix):
        raise CapsuleVerificationError("diff header is malformed")
    payload = line[len(prefix) :].rstrip(b"\r\n")

    # The two path fields are tokenised INDEPENDENTLY, because Git quotes each
    # side on its own merits. A rename from an ASCII name to a non-ASCII one
    # emits a mixed header:
    #
    #     diff --git a/ascii.txt "b/\\303\\251.txt"
    #
    # An earlier version branched on whether the FIRST field was quoted and then
    # handled both the same way, so a mixed header fell into the unquoted path,
    # found no bare " b/" delimiter, and raised "diff header is malformed" --
    # which aborts the whole capture, since `capture` inventories immediately.
    before, index = _take_header_field(payload, 0, b"a/")
    while index < len(payload) and payload[index] == ord(" "):
        index += 1
    after, index = _take_header_field(payload, index, b"b/")
    if index != len(payload):
        raise CapsuleVerificationError("diff header is malformed")
    return _decode_git_path(before), _decode_git_path(after)


def _take_header_field(payload: bytes, start: int, prefix: bytes) -> tuple[bytes, int]:
    """Consume one `a/...` or `b/...` field, quoted or not.

    Quoted is unambiguous. Unquoted is not: Git does NOT quote an ordinary
    space, so `a/a b.txt b/a b.txt` is one valid header with four words. For the
    `a/` field the end is found by locating the following ` b/` or ` "b/`
    delimiter; for the trailing `b/` field it simply runs to the end.
    """
    if start >= len(payload):
        raise CapsuleVerificationError("diff header is malformed")
    if payload[start] == ord('"'):
        index = start + 1
        escaped = False
        while index < len(payload):
            current = payload[index]
            if current == ord('"') and not escaped:
                return payload[start : index + 1], index + 1
            escaped = current == ord("\\") and not escaped
            index += 1
        raise CapsuleVerificationError("diff header is malformed")

    if not payload[start:].startswith(prefix):
        raise CapsuleVerificationError("diff header is malformed")

    if prefix == b"b/":
        return payload[start:], len(payload)

    # Unquoted `a/` field: find the delimiter that begins the `b/` field.
    # Prefer the split where both sides name the same path -- the non-rename
    # case, and the common one -- and otherwise take the first structurally
    # valid split.
    candidates: list[int] = []
    for delimiter in (b' "b/', b" b/"):
        offset = start
        while True:
            found = payload.find(delimiter, offset)
            if found == -1:
                break
            candidates.append(found)
            offset = found + 1
    if not candidates:
        raise CapsuleVerificationError("diff header is malformed")
    for candidate in sorted(candidates):
        left = payload[start:candidate]
        right = payload[candidate + 1 :]
        if right.startswith(b'"'):
            continue
        if left[len(prefix) :] == right[len(b"b/") :]:
            return left, candidate
    return payload[start : min(candidates)], min(candidates)


def _split_quoted_header_tokens(payload: bytes) -> list[bytes]:
    """Tokenise a header whose paths are C-quoted by Git."""
    tokens: list[bytes] = []
    index = 0
    while index < len(payload):
        while index < len(payload) and payload[index] == ord(" "):
            index += 1
        if index >= len(payload):
            break
        start = index
        if payload[index] == ord('"'):
            index += 1
            escaped = False
            while index < len(payload):
                current = payload[index]
                if current == ord('"') and not escaped:
                    index += 1
                    break
                if current == ord("\\") and not escaped:
                    escaped = True
                else:
                    escaped = False
                index += 1
            else:
                raise CapsuleVerificationError("diff header is malformed")
        else:
            while index < len(payload) and payload[index] != ord(" "):
                index += 1
        tokens.append(payload[start:index])
    return tokens


def _trim_unified_header(value: bytes) -> bytes:
    """Drop the trailing TAB field from a unified-diff `---`/`+++` path.

    The unified diff format allows `<path>TAB<timestamp>`, and Git emits the
    tab whenever the path would otherwise be ambiguous -- which includes any
    path containing a space. So `--- a/a b.txt` actually arrives as
    `--- a/a b.txt` + TAB.

    Leaving it on made `_safe_manifest_path` reject the path as unsafe, because
    a tab is not printable. That fired only for paths with spaces, which is why
    it went unseen; this repository tracks 186 of them.
    """
    index = value.find(b"\t")
    return value if index == -1 else value[:index]


def _strip_diff_prefix(value: str, prefix: str) -> str | None:
    if value == "/dev/null":
        return None
    if not value.startswith(prefix):
        raise CapsuleVerificationError("diff path prefix is malformed")
    return _safe_manifest_path(value[len(prefix) :])


def _diff_atoms(
    content: bytes,
    plane: PlaneId,
    source_digest: str,
) -> list[dict[str, object]]:
    if not content:
        return []
    lines = content.splitlines(keepends=True)
    starts = [
        index for index, line in enumerate(lines) if line.startswith(b"diff --git ")
    ]
    if not starts:
        return [
            _new_atom(
                source_plane=plane,
                source_commit=source_digest,
                path_before=None,
                path_after=None,
                blob_before=None,
                blob_after=None,
                mode_before=None,
                mode_after=None,
                exact_diff_digest=_sha256(content),
            )
        ]
    atoms: list[dict[str, object]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block_lines = lines[start:end]
        block = b"".join(block_lines)
        header_before, header_after = _split_diff_header(block_lines[0])
        path_before = _strip_diff_prefix(header_before, "a/")
        path_after = _strip_diff_prefix(header_after, "b/")
        blob_before: str | None = None
        blob_after: str | None = None
        mode_before: str | None = None
        mode_after: str | None = None
        for line in block_lines[1:]:
            stripped = line.rstrip(b"\r\n")
            if stripped.startswith(b"rename from "):
                path_before = _safe_manifest_path(
                    _decode_git_path(stripped[len(b"rename from ") :])
                )
            elif stripped.startswith(b"rename to "):
                path_after = _safe_manifest_path(
                    _decode_git_path(stripped[len(b"rename to ") :])
                )
            elif stripped.startswith(b"old mode "):
                mode_before = stripped[len(b"old mode ") :].decode("ascii")
            elif stripped.startswith(b"new mode "):
                mode_after = stripped[len(b"new mode ") :].decode("ascii")
            elif stripped.startswith(b"new file mode "):
                mode_before = None
                mode_after = stripped[len(b"new file mode ") :].decode("ascii")
            elif stripped.startswith(b"deleted file mode "):
                mode_before = stripped[len(b"deleted file mode ") :].decode("ascii")
                mode_after = None
            elif stripped.startswith(b"index "):
                match = re.fullmatch(
                    rb"index ([0-9a-f]+)\.\.([0-9a-f]+)(?: ([0-7]{6}))?",
                    stripped,
                )
                if match is None:
                    raise CapsuleVerificationError("diff index identity is malformed")
                old, new, common_mode = match.groups()
                # An all-zero id is Git's "this side does not exist" sentinel,
                # emitted for a binary addition or deletion. It is the right
                # length, so a length check alone accepted forty zeroes as a
                # real blob identity and recorded it as provenance. The absent
                # side must stay null.
                if len(old) in {40, 64} and set(old) != {ord("0")}:
                    blob_before = old.decode("ascii")
                if len(new) in {40, 64} and set(new) != {ord("0")}:
                    blob_after = new.decode("ascii")
                if common_mode is not None:
                    mode_before = mode_before or common_mode.decode("ascii")
                    mode_after = mode_after or common_mode.decode("ascii")
            elif stripped.startswith(b"--- "):
                path_before = _strip_diff_prefix(
                    _decode_git_path(_trim_unified_header(stripped[len(b"--- ") :])),
                    "a/",
                )
            elif stripped.startswith(b"+++ "):
                path_after = _strip_diff_prefix(
                    _decode_git_path(_trim_unified_header(stripped[len(b"+++ ") :])),
                    "b/",
                )
        if mode_before is not None and not _MODE.fullmatch(mode_before):
            raise CapsuleVerificationError("diff old mode is malformed")
        if mode_after is not None and not _MODE.fullmatch(mode_after):
            raise CapsuleVerificationError("diff new mode is malformed")
        atoms.append(
            _new_atom(
                source_plane=plane,
                source_commit=source_digest,
                path_before=path_before,
                path_after=path_after,
                blob_before=blob_before,
                blob_after=blob_after,
                mode_before=mode_before,
                mode_after=mode_after,
                exact_diff_digest=_sha256(block),
            )
        )
    return atoms


def _history_atom(
    reader: _VerifiedCapsuleReader,
    root: Path,
    plane: PlaneId,
) -> dict[str, object]:
    identity = _read_json(reader, root / "identity.json")
    if not isinstance(identity, dict):
        raise CapsuleVerificationError("history identity must be an object")
    subject = identity.get("subject_id")
    object_format = identity.get("object_format")
    bundle_ref = identity.get("bundle_ref")
    expected_fields = {
        "bundle_ref",
        "bundle_scope",
        "eligibility",
        "object_format",
        "plane_id",
        "schema_version",
        "sensitivity",
        "status",
        "subject_id",
        "verification",
    }
    if (
        set(identity) != expected_fields
        or identity.get("plane_id") != plane.value
        or identity.get("bundle_scope") != "destination-owned-exact-ref"
        or identity.get("schema_version") != "1"
        or bundle_ref != "refs/heads/master"
        or object_format not in {"sha1", "sha256"}
    ):
        raise CapsuleVerificationError("history identity is malformed")
    _require_disposition(identity, _OPAQUE_DISPOSITION)
    expected_length = 40 if object_format == "sha1" else 64
    if (
        not isinstance(subject, str)
        or len(subject) != expected_length
        or not _HEX_40_OR_64.fullmatch(subject)
    ):
        raise CapsuleVerificationError("history subject identity is malformed")
    if not _nonempty_string(bundle_ref):
        raise CapsuleVerificationError("history bundle ref is malformed")
    refs = reader.read(root / "refs.txt")
    expected_ref = f"{subject} {bundle_ref}\n".encode("utf-8")
    if refs != expected_ref:
        raise CapsuleVerificationError("history refs disagree with identity metadata")
    bundle = reader.read(root / "repository.bundle")
    declaration = f"{subject} {bundle_ref}\n".encode("utf-8")
    if declaration not in bundle.split(b"\n\n", 1)[0] + b"\n":
        raise CapsuleVerificationError("bundle header disagrees with history identity")
    evidence_digest = _sha256(
        canonical_json_bytes(
            {
                "bundle_sha256": _sha256(bundle),
                "identity_sha256": _sha256(canonical_json_bytes(identity)),
                "refs_sha256": _sha256(refs),
            }
        )
    )
    return _new_atom(
        source_plane=plane,
        source_commit=subject,
        path_before=None,
        path_after=None,
        blob_before=None,
        blob_after=None,
        mode_before=None,
        mode_after=None,
        exact_diff_digest=evidence_digest,
    )


def _require_disposition(
    metadata: dict[str, object],
    expected: tuple[str, str, str, str],
) -> None:
    actual = (
        metadata.get("sensitivity"),
        metadata.get("eligibility"),
        metadata.get("verification"),
        metadata.get("status"),
    )
    if actual != expected:
        raise CapsuleVerificationError("plane disposition metadata is inconsistent")


def _secret_exclusions(metadata: dict[str, object]) -> tuple[str, ...]:
    value = metadata.get("secret_path_exclusions")
    if not isinstance(value, list):
        raise CapsuleVerificationError("secret exclusion metadata is invalid")
    exclusions = tuple(_safe_manifest_path(item) for item in value)
    if len(set(exclusions)) != len(exclusions) or list(exclusions) != sorted(
        exclusions, key=lambda item: item.encode("utf-8")
    ):
        raise CapsuleVerificationError("secret exclusion metadata is inconsistent")
    return exclusions


def _validate_manifest_entry(
    entry: dict[str, object],
    *,
    plane: PlaneId,
) -> tuple[str, str | None]:
    if set(entry) != _MANIFEST_ENTRY_FIELDS:
        raise CapsuleVerificationError("manifest entry is invalid")
    path = _safe_manifest_path(entry.get("path"))
    inclusion = entry.get("inclusion")
    allowed = (
        frozenset({"metadata-only", "redacted", "excluded"})
        if plane is PlaneId.LOCAL_TRACKED
        else frozenset({"copied", "redacted", "excluded"})
    )
    if not isinstance(inclusion, str) or inclusion not in allowed:
        raise CapsuleVerificationError("manifest inclusion is not verifiable")
    if inclusion == "redacted":
        if (
            entry.get("kind") != "redacted"
            or entry.get("reason") != "secret-name"
            or entry.get("mode") is not None
            or entry.get("size") is not None
            or entry.get("sha256") is not None
        ):
            raise CapsuleVerificationError("redacted manifest metadata is invalid")
        return path, "redacted-evidence-ineligible"
    if inclusion in {"copied", "metadata-only"}:
        mode = entry.get("mode")
        size = entry.get("size")
        digest = entry.get("sha256")
        if (
            entry.get("kind") != "file"
            or not isinstance(mode, int)
            or isinstance(mode, bool)
            or mode < 0
            or mode > 0o7777
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(digest, str)
            or not _HEX_64.fullmatch(digest)
        ):
            raise CapsuleVerificationError(f"{inclusion} manifest metadata is invalid")
        if inclusion == "copied" and entry.get("reason") not in {
            "untracked",
            "ignored",
        }:
            raise CapsuleVerificationError("copied manifest reason is invalid")
        if (
            inclusion == "metadata-only"
            and entry.get("reason") != "tracked-worktree-inventory"
        ):
            raise CapsuleVerificationError("metadata-only manifest metadata is invalid")
        return path, None

    reason = entry.get("reason")
    kind = entry.get("kind")
    mode = entry.get("mode")
    requires_mode = isinstance(reason, str) and reason not in {
        "gitlink-not-followed",
        "missing-from-worktree",
    }
    if (
        not isinstance(reason, str)
        or reason not in _EXCLUDED_KINDS
        or not isinstance(kind, str)
        or kind not in _EXCLUDED_KINDS[reason]
        or (reason == "gitlink-not-followed" and mode != 0o160000)
        or (reason == "missing-from-worktree" and mode is not None)
        or (requires_mode and not isinstance(mode, int))
        or isinstance(mode, bool)
        or (requires_mode and (mode < 0 or mode > 0o7777))
        or entry.get("size") is not None
        or entry.get("sha256") is not None
    ):
        raise CapsuleVerificationError("excluded manifest metadata is invalid")
    return path, "excluded-evidence-ineligible"


def _manifest_entries(
    reader: _VerifiedCapsuleReader,
    path: Path,
    *,
    plane: PlaneId,
    metadata: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, str]]:
    value = _read_json(reader, path)
    if not isinstance(value, list) or not all(
        isinstance(entry, dict) for entry in value
    ):
        raise CapsuleVerificationError("file manifest must be an array of objects")
    blockers: dict[str, str] = {}
    redacted: set[str] = set()
    seen: set[str] = set()
    for entry in value:
        entry_path, blocker = _validate_manifest_entry(entry, plane=plane)
        if entry_path in seen:
            raise CapsuleVerificationError("manifest contains duplicate paths")
        seen.add(entry_path)
        if entry.get("inclusion") == "redacted":
            redacted.add(entry_path)
        if blocker is not None:
            blockers[entry_path] = blocker
    if set(_secret_exclusions(metadata)) != redacted:
        raise CapsuleVerificationError(
            "manifest disposition exclusions are inconsistent"
        )
    _require_disposition(
        metadata,
        _REDACTED_DISPOSITION if redacted else _ORDINARY_DISPOSITION,
    )
    return value, blockers


def _file_atom(
    entry: dict[str, object],
    *,
    plane: PlaneId,
    source_digest: str,
    before: bool,
    exact_digest: str,
) -> dict[str, object]:
    path = _safe_manifest_path(entry.get("path"))
    content_digest = _optional_digest(entry.get("sha256"))
    mode = _mode(entry.get("mode"), entry.get("kind"))
    return _new_atom(
        source_plane=plane,
        source_commit=source_digest,
        path_before=path if before else None,
        path_after=path,
        blob_before=None,
        blob_after=content_digest,
        mode_before=None,
        mode_after=mode,
        exact_diff_digest=exact_digest,
    )


def _item_for_atom(
    atom: dict[str, object],
    blockers: tuple[str, ...] = (),
) -> dict[str, object]:
    atom_id = str(atom["atom_id"])
    item_id = "item-" + _sha256(atom_id.encode("utf-8"))
    initial = {
        "atom_ids": [atom_id],
        "classification_state": "captured",
        "disposition": None,
        "item_id": item_id,
        "primary_lane": "preservation-admin",
    }
    revision_id = "revision-" + _sha256(canonical_json_bytes(initial))
    return {
        "item_id": item_id,
        "revision_id": revision_id,
        "atom_ids": [atom_id],
        "primary_lane": "preservation-admin",
        "classification_state": "captured",
        "disposition": None,
        "required_gate_ids": [],
        "dependencies": [],
        "blockers": list(blockers),
        "required_profiles": [],
        "replacement_item_id": None,
        "notes": "Locally inventoried capsule evidence; no salvage intent inferred.",
    }


def inventory_change_universe(capsule: Path) -> dict:
    """Inventory a sealed capsule without inferring salvage intent.

    The authenticated provenance root is a local-unanchored evidence identity,
    not a canonical truth claim.
    """

    reader = _VerifiedCapsuleReader(capsule)
    root = reader.root
    capsule_digest = reader.provenance_root
    atoms: list[dict[str, object]] = []
    atom_blockers: dict[str, set[str]] = defaultdict(set)

    def add_atom(atom: dict[str, object], *blockers: str) -> None:
        atoms.append(atom)
        atom_blockers[str(atom["atom_id"])].update(blockers)

    for plane in (PlaneId.REMOTE_MAIN, PlaneId.REMOTE_PR, PlaneId.LOCAL_HISTORY):
        add_atom(
            _history_atom(reader, root / plane.value, plane),
            "opaque-preservation-ineligible",
        )

    index_root = root / PlaneId.LOCAL_INDEX.value
    index_bytes = reader.read(index_root / "index.raw")
    index_metadata = _read_json(reader, index_root / "metadata.json")
    if not isinstance(index_metadata, dict):
        raise CapsuleVerificationError("index metadata must be an object")
    _secret_exclusions(index_metadata)
    _require_disposition(index_metadata, _OPAQUE_DISPOSITION)
    index_digest = _sha256(index_bytes)
    if index_metadata.get("index_sha256") != index_digest:
        raise CapsuleVerificationError(
            "index metadata disagrees with exact index bytes"
        )
    staged_diff = reader.read(index_root / "staged.diff")
    add_atom(
        _new_atom(
            source_plane=PlaneId.LOCAL_INDEX,
            source_commit=index_digest,
            path_before=None,
            path_after=None,
            blob_before=None,
            blob_after=index_digest,
            mode_before=None,
            mode_after=None,
            exact_diff_digest=_sha256(staged_diff),
        ),
        "opaque-preservation-ineligible",
    )
    for atom in _diff_atoms(staged_diff, PlaneId.LOCAL_INDEX, index_digest):
        add_atom(atom, "opaque-preservation-ineligible")

    tracked_root = root / PlaneId.LOCAL_TRACKED.value
    tracked_diff = reader.read(tracked_root / "unstaged.diff")
    tracked_metadata = _read_json(reader, tracked_root / "metadata.json")
    if not isinstance(tracked_metadata, dict):
        raise CapsuleVerificationError("tracked metadata must be an object")
    tracked_entries, tracked_blockers = _manifest_entries(
        reader,
        tracked_root / "manifest.json",
        plane=PlaneId.LOCAL_TRACKED,
        metadata=tracked_metadata,
    )
    tracked_digest = _sha256(tracked_diff + canonical_json_bytes(tracked_entries))
    for atom in _diff_atoms(tracked_diff, PlaneId.LOCAL_TRACKED, tracked_digest):
        add_atom(atom)
    for entry in tracked_entries:
        atom = _file_atom(
            entry,
            plane=PlaneId.LOCAL_TRACKED,
            source_digest=tracked_digest,
            before=True,
            exact_digest=_sha256(tracked_diff),
        )
        blocker = tracked_blockers.get(str(entry["path"]))
        add_atom(atom, *((blocker,) if blocker is not None else ()))

    untracked_root = root / PlaneId.LOCAL_UNTRACKED.value
    untracked_metadata = _read_json(reader, untracked_root / "metadata.json")
    if not isinstance(untracked_metadata, dict):
        raise CapsuleVerificationError("untracked metadata must be an object")
    untracked_entries, untracked_blockers = _manifest_entries(
        reader,
        untracked_root / "manifest.json",
        plane=PlaneId.LOCAL_UNTRACKED,
        metadata=untracked_metadata,
    )
    untracked_digest = _sha256(canonical_json_bytes(untracked_entries))
    for entry in untracked_entries:
        atom = _file_atom(
            entry,
            plane=PlaneId.LOCAL_UNTRACKED,
            source_digest=untracked_digest,
            before=False,
            exact_digest=_sha256(canonical_json_bytes(entry)),
        )
        if entry.get("inclusion") == "copied":
            payload = reader.read(
                untracked_root / "payload" / PurePosixPath(str(entry["path"]))
            )
            if entry.get("size") != len(payload) or entry.get("sha256") != _sha256(
                payload
            ):
                raise CapsuleVerificationError(
                    "untracked payload disagrees with manifest metadata"
                )
        blocker = untracked_blockers.get(str(entry["path"]))
        add_atom(atom, *((blocker,) if blocker is not None else ()))

    by_id: dict[str, dict[str, object]] = {}
    for atom in atoms:
        atom_id = str(atom["atom_id"])
        if atom_id in by_id:
            raise CapsuleVerificationError("inventory produced a duplicate atom ID")
        by_id[atom_id] = atom
    ordered_atoms = [by_id[atom_id] for atom_id in sorted(by_id)]
    items = sorted(
        (
            _item_for_atom(
                atom,
                tuple(sorted(atom_blockers[str(atom["atom_id"])])),
            )
            for atom in ordered_atoms
        ),
        key=lambda item: str(item["item_id"]),
    )
    data = {
        "schema_version": "1.0.0",
        "state_id": "capsule-" + capsule_digest,
        "capsule_root": capsule_digest,
        "atoms": ordered_atoms,
        "items": items,
    }
    errors = validate_manifest(data)
    if errors:
        raise CapsuleVerificationError(
            "generated manifest is invalid: " + "; ".join(errors)
        )
    return data
