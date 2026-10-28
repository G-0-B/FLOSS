"""Bounded first-INSTALL preparation; never remove or restore live directories.

Records are local observations, not ownership or historical attribution proofs.
Only the measured Windows no-replace primitive is supported. Qualification uses
retained synthetic cross-parent operands on the same volume. ACL/scanner/crash
durability and hostile same-user source substitution remain outside this proof.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import sys
from typing import Callable


class PreparationError(OSError):
    """Preparation refused before publication; all existing paths retained."""


def _plain_ancestry(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    for part in [absolute, *absolute.parents]:
        try:
            metadata = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 1024:
            raise PreparationError(f"UNSUPPORTED linked/reparse ancestry: {part}")
    return absolute.resolve()


def validate_private_root(private: Path, forbidden: tuple[Path, ...]) -> Path:
    resolved = _plain_ancestry(private)
    for root in forbidden:
        boundary = _plain_ancestry(root)
        if resolved.is_relative_to(boundary) or boundary.is_relative_to(resolved):
            raise PreparationError(f"private root overlaps discovery/source/output tree: {root}")
    return resolved


def inventory_plain(directory: Path, *, generated_dirs, generated_files,
                    generated_suffixes, marker_name: str, marker_temp_prefix: str) -> dict:
    """Typed plain-node coverage, including empty dirs, with F10 exclusions.

    Do not use is_file/is_dir before inspecting reparse metadata: WSL link nodes
    can report regular lstat mode but cannot be opened through Windows.
    """
    root = _plain_ancestry(directory)
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise PreparationError(f"not a plain directory: {directory}")
    result = {}
    pending = [root]
    while pending:
        base = pending.pop()
        for child in sorted(base.iterdir()):
            metadata = child.lstat()
            rel = child.relative_to(root).as_posix()
            if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 1024:
                raise PreparationError(f"UNSUPPORTED payload link/reparse: {child}")
            if rel == marker_name or rel.startswith(marker_temp_prefix):
                continue
            if stat.S_ISDIR(metadata.st_mode):
                if child.name in generated_dirs:
                    continue
                result[rel] = {"kind": "directory"}
                pending.append(child)
            elif stat.S_ISREG(metadata.st_mode):
                if child.name in generated_files or child.name.endswith(generated_suffixes):
                    continue
                data = child.read_bytes()
                result[rel] = {"kind": "file", "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            else:
                raise PreparationError(f"UNSUPPORTED special payload node: {child}")
    return dict(sorted(result.items()))


def _write_record(path: Path, payload: dict) -> None:
    # Retain a failed temporary record rather than deleting uncertain content.
    temporary = path.with_name(path.name + ".next-" + secrets.token_hex(8))
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
    os.replace(temporary, path)


def publish_no_replace(stage: Path, target: Path) -> None:
    if sys.platform != "win32":
        raise PreparationError("UNSUPPORTED publication backend: only qualified Windows rename is enabled")
    os.rename(stage, target)


def qualify_publication(private: Path, target_parent: Path) -> Path:
    """Retained absent-success + five refusal controls, same volume, cross-parent.

    Synthetic targets remain outside discovery roots. This qualifies the native
    primitive on that volume, not target ACLs or third-party scanner behavior.
    """
    if sys.platform != "win32":
        raise PreparationError("UNSUPPORTED publication backend on this platform")
    if private.stat().st_dev != target_parent.stat().st_dev:
        raise PreparationError("UNSUPPORTED cross-volume publication")
    area = private / ("qualification-" + secrets.token_hex(8))
    area.mkdir()
    rows = []
    try:
        for kind in ["absent", "empty", "nonempty", "file", "dangling", "dirlink"]:
            fixture = area / kind
            (fixture / "private").mkdir(parents=True)
            (fixture / "discovery").mkdir()
            source, target = fixture / "private/staged", fixture / "discovery/live"
            source.mkdir()
            (source / "probe.bin").write_bytes(b"synthetic publication control")
            if kind in {"empty", "nonempty"}:
                target.mkdir()
                if kind == "nonempty":
                    (target / "foreign.bin").write_bytes(b"retain foreign control")
            elif kind == "file":
                target.write_bytes(b"retain foreign control")
            elif kind == "dangling":
                os.symlink(str(fixture / "missing"), target)
            elif kind == "dirlink":
                elsewhere = fixture / "elsewhere"
                elsewhere.mkdir()
                os.symlink(str(elsewhere), target, target_is_directory=True)
            before = target.lstat() if os.path.lexists(target) else None
            try:
                publish_no_replace(source, target)
            except FileExistsError as exc:
                after = target.lstat()
                good = kind != "absent" and before is not None and before.st_ino == after.st_ino and source.is_dir()
                rows.append(dict(kind=kind, refused=True, preserved_identity=good, errno=exc.errno, winerror=getattr(exc, "winerror", None)))
                if not good:
                    raise PreparationError("no-replace refusal control failed")
            else:
                good = kind == "absent" and not source.exists() and (target / "probe.bin").read_bytes() == b"synthetic publication control"
                rows.append(dict(kind=kind, renamed=True, absent_success=good))
                if not good:
                    raise PreparationError("no-replace absent/existing control failed")
    except OSError as exc:
        reason = "QUALIFICATION_NOT_MEASURED: link privilege" if getattr(exc, "winerror", None) == 1314 else "native publication qualification"
        _write_record(area / "qualification.json", dict(status="UNSUPPORTED", platform=sys.platform, rows=rows, reason=reason, error=str(exc)))
        raise PreparationError(f"UNSUPPORTED {reason}: {exc}") from exc
    _write_record(area / "qualification.json", dict(status="QUALIFIED_LOCAL_PRIMITIVE", platform=sys.platform,
        volume=private.stat().st_dev, target_parent=str(target_parent), rows=rows,
        limits="Synthetic cross-parent controls only; no target ACL, scanner, crash or source-CAS proof"))
    return area / "qualification.json"


def _path_key(path: Path | str) -> str:
    return os.path.normcase(os.path.realpath(path))


def persist_deferred_report(private: Path, payload: dict) -> Path:
    """Idempotent observation only; no new payload copy or promotion facility."""
    content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    private.mkdir(parents=True, exist_ok=True)
    destination = private / ("update-" + digest + ".json")
    _plain_ancestry(destination)
    if os.path.lexists(destination):
        if destination.read_text(encoding="utf-8") != content:
            raise PreparationError(f"deferred report collision: {destination}")
        return destination
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
    return destination


def pending_for_target(private: Path, target: Path | None, workspace: Path,
                       inventory: Callable[[Path], dict], marker_name: str,
                       active_targets: tuple[Path, ...] = ()) -> list[str]:
    if not os.path.lexists(private):
        return []
    _plain_ancestry(private)
    messages = []
    for child in sorted(private.iterdir()):
        if not child.name.startswith("install-"):
            continue
        _plain_ancestry(child)
        record = child / "transaction.json"
        try:
            _plain_ancestry(record)
            payload = json.loads(record.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("record is not an object")
            if (type(payload.get("schema_version")) is not int or payload["schema_version"] != 1
                    or payload.get("phase") not in {"PREPARING", "PREPARED", "FAILED", "COMMITTED"}
                    or not all(isinstance(payload.get(k), str) and Path(payload[k]).is_absolute()
                               for k in ("workspace_root", "target", "source_path"))
                    or not isinstance(payload.get("expected_inventory"), dict)
                    or not isinstance(payload.get("marker_content"), str)):
                raise ValueError("invalid or incomplete transaction record")
            if payload.get("phase") == "COMMITTED":
                continue
            if _path_key(payload["workspace_root"]) != _path_key(workspace):
                messages.append(f"PENDING FOREIGN_WORKSPACE_RECORD: {record}; recorded={payload['workspace_root']}; current={workspace}; no action")
                continue
            if target is not None and _path_key(payload["target"]) != _path_key(target):
                continue
            if target is None:
                label = "ACTIVE_RECORD" if _path_key(payload["target"]) in {_path_key(p) for p in active_targets} else "ORPHAN_RECORD"
                messages.append(f"PENDING {label}: {record}; target={payload['target']}; no resume")
                continue
            label = "RECOVERY_NEEDED"
            if not os.path.lexists(child / "payload") and os.path.lexists(target):
                marker = target / marker_name
                _plain_ancestry(marker)
                if marker.read_text(encoding="utf-8") == payload.get("marker_content") and inventory(target) == payload.get("expected_inventory"):
                    label = "CONTENT_MATCH_UNACKNOWLEDGED"
            messages.append(f"PENDING {label}: {target}; retained record {record}; observation only, no resume")
        except (OSError, ValueError, TypeError) as exc:
            messages.append(f"PENDING RECOVERY_NEEDED: unreadable record/operands {record}: {exc}")
    return messages


def prepare_install(source: Path, target: Path, workspace: Path, private_root: Path,
                    discovery_roots: tuple[Path, ...], inventory: Callable[[Path], dict],
                    copy_payload: Callable, marker_content: str, marker_name: str,
                    marker_temp_prefix: str, publish_marker: Callable,
                    qualification_cache: dict | None = None,
                    registry_observation: dict | None = None) -> tuple[str, str]:
    private = validate_private_root(private_root, (*discovery_roots, source))
    _plain_ancestry(target.parent)
    before = inventory(source)
    # Reserved control files in a source are not silently overwritten/omitted.
    if any(p.name == marker_name or p.name.startswith(marker_temp_prefix) for p in source.iterdir()):
        raise PreparationError("UNSUPPORTED reserved control file in source")
    source_files = {k: v["sha256"] for k, v in before.items() if v["kind"] == "file"}
    if json.loads(marker_content).get("installed_files") != source_files:
        raise PreparationError("SOURCE_MOVED: selected marker differs from source byte inventory")
    private.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    cache_key = (str(private), target.parent.stat().st_dev)
    if qualification_cache is not None and cache_key in qualification_cache:
        qualification = qualification_cache[cache_key]
    else:
        qualification = qualify_publication(private, target.parent)
        if qualification_cache is not None:
            qualification_cache[cache_key] = qualification
    container = private / ("install-" + secrets.token_hex(16))
    container.mkdir()
    stage = container / "payload"
    record_path = container / "transaction.json"
    record = dict(schema_version=1, workspace_root=str(workspace.resolve()), source_path=str(source),
        source_identity="Observed worktree bytes; BYTES_NOT_FROZEN unless committed/retained independently",
        target=str(target), expected_inventory=before, marker_content=marker_content,
        qualification=str(qualification), registry_observation=registry_observation,
        phase="PREPARING")
    _write_record(record_path, record)
    publish_conflict = False
    try:
        copy_payload(source, stage)
        if inventory(stage) != before or inventory(source) != before:
            raise PreparationError("SOURCE_MOVED or staged representation differs; retained")
        publish_marker(stage, marker_content)
        marker = stage / marker_name
        _plain_ancestry(marker)
        if marker.read_text(encoding="utf-8") != marker_content or inventory(stage) != before or inventory(source) != before:
            raise PreparationError("SOURCE_MOVED or marker/stage changed before publication")
        record["phase"] = "PREPARED"
        _write_record(record_path, record)
        # Revalidate path boundaries after copy callbacks; no source-CAS claim.
        validate_private_root(private, (*discovery_roots, source))
        _plain_ancestry(stage)
        _plain_ancestry(target.parent)
        try:
            publish_no_replace(stage, target)
        except FileExistsError:
            publish_conflict = True
            raise
    except OSError as exc:
        record.update(phase="FAILED", error=str(exc))
        try:
            _write_record(record_path, record)
        except OSError as record_error:
            return "FAILED", f"{exc}; record update failed {record_error}; retained {container}"
        outcome = "CONFLICT" if publish_conflict else "FAILED"
        return outcome, f"{exc}; live name untouched by cleanup; retained {container}; target_present={os.path.lexists(target)} stage_present={os.path.lexists(stage)}"
    # Lost acknowledgement is intentionally left pending, never rolled back.
    record["phase"] = "COMMITTED"
    try:
        _write_record(record_path, record)
    except OSError as exc:
        return "FAILED", f"published but acknowledgement failed: {exc}; inspect {record_path}"
    return "WROTE", f"{target} (INSTALL); record {record_path}"
