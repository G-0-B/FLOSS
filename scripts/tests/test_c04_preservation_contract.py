"""Approved preservation contract: actual synthetic install and failure paths."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


def load():
    scripts = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location("c04_contract_subject", scripts / "materialize_shared_skill_surface.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def setup(tmp_path):
    m = load()
    workspace = tmp_path / "workspace"
    source = workspace / "corpus" / "s"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_bytes(b"synthetic source\r\n")
    roots = workspace / "installed"
    roots.mkdir()
    skill = {"skill_name": "s", "resolved_path": str(source)}
    return m, workspace, source, roots, skill


def install(m, workspace, roots, skill, **flags):
    return m.install_skill_projection("test", skill, roots, "test", workspace_root=workspace,
                                      check=flags.get("check", False), dry_run=flags.get("dry_run", False))


def records(workspace):
    return list(workspace.glob(".agent-surface/harvest/skill-preparation/**/transaction.json"))


def symlink_or_skip(target, link, *, directory=False):
    try:
        os.symlink(str(target), link, target_is_directory=directory)
    except OSError as exc:
        pytest.skip(f"symlink capability unavailable: {exc}")


def seed(m, workspace, source, roots, skill, path=None):
    target = path or roots / "s"
    target.mkdir()
    (target / "SKILL.md").write_bytes((source / "SKILL.md").read_bytes())
    marker = m.serialize_marker(skill, "test", workspace, installed_files=m.payload_digests(target))
    (target / m.MANAGED_MARKER).write_text(marker, encoding="utf-8")
    return target


@pytest.mark.skipif(os.name != "nt", reason="first publication backend intentionally Windows-only")
def test_install_copies_outside_discovery_and_publishes_matching_marker(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    original = m._copy_payload
    seen = []
    def copy(src, dst):
        assert not Path(dst).is_relative_to(roots)
        assert not (roots / "s").exists()
        seen.append(Path(dst))
        return original(src, dst)
    monkeypatch.setattr(m, "_copy_payload", copy)
    lines, changed = install(m, w, roots, skill)
    assert changed and seen and (roots / "s").is_dir(), lines
    marker = json.loads((roots / "s" / m.MANAGED_MARKER).read_text())
    assert marker["installed_files"] == m.payload_digests(roots / "s") == m.payload_digests(source)
    assert any(json.loads(p.read_text())["phase"] == "COMMITTED" for p in records(w))


@pytest.mark.parametrize("failure", ["partial_copy", "marker", "source_moved", "stage_changed", "wrong_marker"])
@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_failed_preparation_never_creates_live_partial(tmp_path, monkeypatch, failure):
    m, w, source, roots, skill = setup(tmp_path)
    original_copy, original_marker = m._copy_payload, m.publish_marker
    def copy(src, dst):
        if failure == "partial_copy":
            Path(dst).mkdir()
            (Path(dst) / "partial.bin").write_bytes(b"retain truncated bytes")
            raise OSError("synthetic partial copy")
        original_copy(src, dst)
        if failure == "source_moved":
            (source / "SKILL.md").write_bytes(b"independent source edit")
    def marker(dst, content):
        if failure == "marker":
            raise OSError("synthetic marker failure")
        original_marker(dst, content if failure != "wrong_marker" else "{}")
        if failure == "stage_changed":
            (Path(dst) / "late-learning.bin").write_bytes(b"retain independent stage edit")
    monkeypatch.setattr(m, "_copy_payload", copy)
    monkeypatch.setattr(m, "publish_marker", marker)
    def forbidden(*args):
        raise AssertionError("private preparation reached legacy cleanup")
    monkeypatch.setattr(m, "remove_path", forbidden)
    monkeypatch.setattr(m, "_discard_failed_install", forbidden)
    lines, changed = install(m, w, roots, skill)
    assert not (roots / "s").exists(), lines
    assert records(w), "failed private preparation must stay inspectable"
    assert changed and any("FAILED" in line or "SOURCE_MOVED" in line for line in lines), lines
    again, drift = install(m, w, roots, skill, check=True)
    assert drift and any("PENDING" in line for line in again), again


@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_target_appearing_during_copy_stays_at_live_name(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    original = m._copy_payload
    def copy(src, dst):
        live = roots / "s"
        live.mkdir()
        (live / "learned.bin").write_bytes(b"foreign independently appeared bytes")
        original(src, dst)
    monkeypatch.setattr(m, "_copy_payload", copy)
    lines, attention = install(m, w, roots, skill)
    assert (roots / "s" / "learned.bin").read_bytes() == b"foreign independently appeared bytes"
    assert records(w) and attention and any("CONFLICT" in line for line in lines), lines


@pytest.mark.parametrize("flags", [{}, {"check": True}, {"dry_run": True}])
def test_update_is_explicit_deferred_and_keeps_live_identity(tmp_path, monkeypatch, flags):
    m, w, source, roots, skill = setup(tmp_path)
    live = seed(m, w, source, roots, skill)
    before = (live.stat().st_ino, (live / "SKILL.md").read_bytes(), (live / m.MANAGED_MARKER).read_bytes())
    (source / "SKILL.md").write_bytes(b"new shared base")
    def forbidden(*args, **kwargs):
        raise AssertionError("live removal/copy/rename reached by frozen UPDATE")
    for name in ["remove_if_unchanged", "remove_path", "_put_back", "_copy_payload"]:
        monkeypatch.setattr(m, name, forbidden)
    lines, attention = install(m, w, roots, skill, **flags)
    assert attention and any("UPDATE_DEFERRED" in line for line in lines), lines
    assert before == (live.stat().st_ino, (live / "SKILL.md").read_bytes(), (live / m.MANAGED_MARKER).read_bytes())
    assert not records(w), "deferred UPDATE is not another payload copy"


@pytest.mark.parametrize("stranded", [False, True])
@pytest.mark.parametrize("flags", [{}, {"check": True}, {"dry_run": True}])
def test_prune_and_restore_are_report_only(tmp_path, monkeypatch, stranded, flags):
    m, w, source, roots, skill = setup(tmp_path)
    name = m.REMOVING_PREFIX + "0123456789abcdef-s" if stranded else "s"
    held = seed(m, w, source, roots, skill, roots / name)
    before = (held.stat().st_ino, (held / "SKILL.md").read_bytes())
    def forbidden(*args, **kwargs):
        raise AssertionError("frozen prune/restore reached live mutation helper")
    for fn in ["remove_if_unchanged", "remove_path", "_put_back"]:
        monkeypatch.setattr(m, fn, forbidden)
    lines, attention = m.prune_stale_projections("test", roots, {"s"} if stranded else set(),
        owner_root=w, check=flags.get("check", False), dry_run=flags.get("dry_run", False))
    expected = "RESTORE_DEFERRED" if stranded else "PRUNE_DEFERRED"
    assert attention and any(expected in line for line in lines), lines
    assert before == (held.stat().st_ino, (held / "SKILL.md").read_bytes())
    if stranded:
        lines, attention = install(m, w, roots, skill)
        assert attention and not (roots / "s").exists() and any("RESTORE_DEFERRED" in line for line in lines)


@pytest.mark.parametrize("outcome,expected", [("UPDATE_DEFERRED", 1), ("PRUNE_DEFERRED", 1), ("UNSUPPORTED", 1), ("FAILED", 1), ("CONFLICT", 1), ("WROTE", 0), ("KEEP", 0)])
def test_plain_cli_reports_unresolved_work_nonzero(tmp_path, monkeypatch, outcome, expected):
    m = load()
    monkeypatch.setattr(sys, "argv", ["skill", "--workspace-root", str(tmp_path)])
    monkeypatch.setattr(m, "materialize", lambda **kwargs: ([f"{outcome} synthetic"], True))
    assert m.main() == expected


@pytest.mark.parametrize("bad", ["inside_target", "contains_target", "inside_config"])
@pytest.mark.skipif(os.name != "nt", reason="Windows INSTALL boundary path")
def test_private_root_overlap_is_refused_without_creating_stage(tmp_path, bad):
    m, w, source, roots, skill = setup(tmp_path)
    private = {"inside_target": roots / "hidden-stage", "contains_target": w,
               "inside_config": w / ".codex/private"}[bad]
    lines, attention = m.install_skill_projection("test", skill, roots, "test", check=False,
        dry_run=False, workspace_root=w, staging_root=private)
    assert attention and any("overlap" in line for line in lines), lines
    assert not (roots / "s").exists()


@pytest.mark.parametrize("shape", [{}, {"workspace_root": "nonsense", "phase": "COMMITTED"}, []])
def test_invalid_pending_record_cannot_be_silently_ignored(tmp_path, shape):
    m, w, source, roots, skill = setup(tmp_path)
    container = w / ".agent-surface/harvest/skill-preparation/install-invalid"
    container.mkdir(parents=True)
    (container / "transaction.json").write_text(json.dumps(shape), encoding="utf-8")
    lines, attention = install(m, w, roots, skill, check=True)
    assert attention and any("PENDING" in line for line in lines), lines


@pytest.mark.parametrize("failure", ["publish_permission", "acknowledgement", "record_before_publish"])
@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_native_and_record_failures_retain_operands(tmp_path, monkeypatch, failure):
    m, w, source, roots, skill = setup(tmp_path)
    native, write_record = m.staging.publish_no_replace, m.staging._write_record
    def publish(stage, target):
        if failure == "publish_permission" and target.parent == roots:
            raise PermissionError("synthetic sharing/permission error")
        return native(stage, target)
    def record(path, payload):
        if failure == "acknowledgement" and payload.get("phase") == "COMMITTED":
            raise OSError("synthetic lost acknowledgement")
        if failure == "record_before_publish" and payload.get("phase") == "PREPARED":
            raise OSError("synthetic record refusal before publication")
        return write_record(path, payload)
    monkeypatch.setattr(m.staging, "publish_no_replace", publish)
    monkeypatch.setattr(m.staging, "_write_record", record)
    lines, attention = install(m, w, roots, skill)
    assert attention and any(line.startswith("FAILED") for line in lines), lines
    assert (roots / "s").exists() == (failure == "acknowledgement")
    assert records(w)
    pending, drift = install(m, w, roots, skill, check=True)
    assert drift and any("PENDING" in line for line in pending), pending
    if failure == "acknowledgement":
        assert any("CONTENT_MATCH_UNACKNOWLEDGED" in line for line in pending), pending
        assert not any("COMMITTED_UNACKNOWLEDGED" in line for line in pending)


def test_unsupported_platform_does_not_copy_into_live_tree(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    monkeypatch.setattr(m.staging.sys, "platform", "linux")
    lines, attention = install(m, w, roots, skill)
    assert attention and any("UNSUPPORTED" in line for line in lines), lines
    assert not (roots / "s").exists()


@pytest.mark.parametrize("directory", [False, True])
def test_unqualified_payload_links_are_refused(tmp_path, directory):
    m, w, source, roots, skill = setup(tmp_path)
    outside = w / "outside"
    outside.mkdir()
    (outside / "learning.txt").write_bytes(b"do not copy linked target")
    symlink_or_skip(outside if directory else outside / "learning.txt", source / "linked", directory=directory)
    lines, attention = install(m, w, roots, skill)
    assert attention and any("UNSUPPORTED" in line for line in lines), lines
    assert not (roots / "s").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_empty_directory_coverage_and_generated_node_type_policy(tmp_path):
    m, w, source, roots, skill = setup(tmp_path)
    (source / "empty").mkdir()
    (source / "desktop.ini").mkdir()
    (source / "desktop.ini/lesson.md").write_bytes(b"real lesson inside named directory")
    (source / "__pycache__").mkdir()
    (source / "__pycache__/noise.pyc").write_bytes(b"generated")
    lines, attention = install(m, w, roots, skill)
    assert any(line.startswith("WROTE") for line in lines), lines
    live = roots / "s"
    assert (live / "empty").is_dir() and (live / "desktop.ini/lesson.md").read_bytes().startswith(b"real lesson")
    assert not (live / "__pycache__").exists()


@pytest.mark.parametrize("mode", ["check", "dry_run"])
def test_read_only_modes_create_no_private_records(tmp_path, mode):
    m, w, source, roots, skill = setup(tmp_path)
    before = sorted(str(p.relative_to(w)) for p in w.rglob("*"))
    install(m, w, roots, skill, **{mode: True})
    assert sorted(str(p.relative_to(w)) for p in w.rglob("*")) == before


@pytest.mark.parametrize("moved", [False, True])
@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_materialize_reports_pending_after_manifest_withdrawal_or_workspace_move(tmp_path, monkeypatch, moved):
    m, w, source, roots, skill = setup(tmp_path)
    def failed_copy(*args):
        raise OSError("retain unfinished transaction")
    monkeypatch.setattr(m, "_copy_payload", failed_copy)
    install(m, w, roots, skill)
    if moved:
        renamed = w.with_name("renamed-workspace")
        w.rename(renamed)
        w = renamed
    manifest = w / "manifest.json"
    manifest.write_text(json.dumps(dict(manifest_version="test", targets={}, skills=[])))
    lines, attention = m.materialize(w, manifest, w / "output", check=True, dry_run=False)
    assert attention and any("PENDING" in line for line in lines), lines


@pytest.mark.skipif(os.name != "nt", reason="Windows path case equivalence")
def test_pending_target_matching_uses_windows_path_equivalence(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    monkeypatch.setattr(m, "_copy_payload", lambda *args: (_ for _ in ()).throw(OSError("failed")))
    install(m, w, roots, skill)
    lines, attention = install(m, w, Path(str(roots).upper()), skill, check=True)
    assert attention and any("PENDING" in line for line in lines), lines


def test_linked_sibling_root_does_not_mask_existing_current_install(tmp_path):
    m, w, source, roots, skill = setup(tmp_path)
    seed(m, w, source, roots, skill)
    other, linked = w / "other", w / "linked-sibling"
    other.mkdir()
    symlink_or_skip(other, linked, directory=True)
    lines, attention = m.install_skill_projection("test", skill, roots, "test", check=True,
        dry_run=False, workspace_root=w, discovery_roots=(linked,))
    assert not attention and any("CHECK OK" in line for line in lines), lines


@pytest.mark.parametrize("mode", ["check", "dry_run"])
def test_unsupported_platform_plan_is_explicit(tmp_path, monkeypatch, mode):
    m, w, source, roots, skill = setup(tmp_path)
    monkeypatch.setattr(m.staging.sys, "platform", "linux")
    lines, attention = install(m, w, roots, skill, **{mode: True})
    assert attention and any("UNSUPPORTED" in line for line in lines), lines
    assert not any("PLAN  WRITE" in line for line in lines)


@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_private_copy_fileexists_is_failure_not_live_publication_conflict(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    def collided(*args):
        raise FileExistsError("synthetic private copy collision")
    monkeypatch.setattr(m, "_copy_payload", collided)
    lines, attention = install(m, w, roots, skill)
    assert attention and any(line.startswith("FAILED") for line in lines), lines


@pytest.mark.parametrize("mode", [[], ["--check"], ["--dry-run"], ["--check", "--dry-run"]])
@pytest.mark.parametrize("outcome", ["UPDATE_DEFERRED", "RESTORE_DEFERRED", "FAILED", "UNSUPPORTED", "PENDING", "CONFLICT", "KEEP", "WROTE"])
def test_cli_mode_outcome_matrix(tmp_path, monkeypatch, mode, outcome):
    m = load()
    attention = outcome not in {"KEEP", "WROTE"}
    changed = outcome == "WROTE"
    monkeypatch.setattr(sys, "argv", ["skill", "--workspace-root", str(tmp_path), *mode])
    monkeypatch.setattr(m, "materialize", lambda **kwargs: ([outcome + " synthetic"], attention or changed))
    failure = outcome in {"FAILED", "UNSUPPORTED", "PENDING", "CONFLICT"}
    deferred = outcome.endswith("_DEFERRED")
    expected = failure or ("--check" in mode and (attention or changed)) or (deferred and "--dry-run" not in mode)
    assert m.main() == int(expected)


def test_update_observation_is_complete_and_idempotent(tmp_path):
    m, w, source, roots, skill = setup(tmp_path)
    live = seed(m, w, source, roots, skill)
    (source / "SKILL.md").write_bytes(b"new base")
    install(m, w, roots, skill)
    install(m, w, roots, skill)
    reports = list(w.glob(".agent-surface/harvest/skill-preparation/update-*.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert report["workspace_root"] == str(w.resolve()) and report["target"] == str(live)
    assert report["baseline"] == report["installed_digests"] != report["source_digests"]
    assert report["observed_live_identity"]["inode"] == live.stat().st_ino
    assert "BYTES_NOT_FROZEN" in report["source_byte_preservation"]


@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_qualification_is_cached_for_one_materialize_volume(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    for name in ["s", "t"]:
        directory = w / "corpus" / name
        directory.mkdir(exist_ok=True)
        (directory / "SKILL.md").write_text(f"---\nname: {name}\ndescription: synthetic\n---\n")
    manifest = w / "manifest.json"
    manifest.write_text(json.dumps(dict(manifest_version="test", targets={"test":dict(enabled=True, scope="repo", install_path="installed")}, skills=[dict(id=n, path=f"corpus/{n}") for n in ["s", "t"]])))
    calls = []
    original = m.staging.qualify_publication
    def qualify(*args):
        calls.append(args)
        return original(*args)
    monkeypatch.setattr(m.staging, "qualify_publication", qualify)
    lines, changed = m.materialize(w, manifest, w / "output", check=False, dry_run=False)
    assert len(calls) == 1 and len(records(w)) == 2, lines


@pytest.mark.skipif(os.name != "nt", reason="Windows publication qualification path")
def test_registry_text_identity_is_distinct_from_byte_inventory(tmp_path):
    m, w, source, roots, skill = setup(tmp_path)
    skill["files"] = {"SKILL.md": "synthetic source\n"}
    lines, changed = install(m, w, roots, skill)
    assert any(line.startswith("WROTE") for line in lines), lines
    observation = json.loads(records(w)[0].read_text())["registry_observation"]
    assert observation["status"] == "V1_TEXT_DIFFERS_FROM_SELECTED_BYTE_INVENTORY"
    assert len(observation["v1_files_sha256"]) == 64 and not observation["atomic_snapshot_qualified"]


@pytest.mark.parametrize("version", [True, 1.0])
def test_pending_record_schema_version_has_strict_integer_type(tmp_path, version):
    m, w, source, roots, skill = setup(tmp_path)
    container = w / ".agent-surface/harvest/skill-preparation/install-invalid"
    container.mkdir(parents=True)
    record = dict(schema_version=version, phase="COMMITTED", workspace_root=str(w), target=str(roots / "s"), source_path=str(source), expected_inventory={}, marker_content="{}")
    (container / "transaction.json").write_text(json.dumps(record))
    lines, attention = install(m, w, roots, skill, check=True)
    assert attention and any("PENDING" in line for line in lines), lines


def test_learning_arriving_during_update_reporting_stays_live(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    live = seed(m, w, source, roots, skill)
    inode = live.stat().st_ino
    (source / "SKILL.md").write_bytes(b"new shared version")
    original = m.staging.persist_deferred_report
    def reporting(*args):
        (live / "learned.bin").write_bytes(b"independent learning during reporting")
        return original(*args)
    monkeypatch.setattr(m.staging, "persist_deferred_report", reporting)
    lines, attention = install(m, w, roots, skill)
    assert attention and any("UPDATE_DEFERRED" in line for line in lines)
    assert live.stat().st_ino == inode and (live / "learned.bin").read_bytes().endswith(b"during reporting")


def test_learning_arriving_during_prune_inspection_stays_live(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    live = seed(m, w, source, roots, skill)
    original = m.projection_owned_by
    def inspected(*args):
        owned = original(*args)
        (live / "learned.bin").write_bytes(b"independent learning during inspection")
        return owned
    monkeypatch.setattr(m, "projection_owned_by", inspected)
    lines, attention = m.prune_stale_projections("test", roots, set(), check=False, dry_run=False, owner_root=w)
    assert attention and any("PRUNE_DEFERRED" in line for line in lines)
    assert (live / "learned.bin").read_bytes().endswith(b"during inspection")


@pytest.mark.skipif(os.name != "nt", reason="create failed Windows INSTALL record")
def test_declared_user_scope_pending_is_not_mislabelled_orphan(tmp_path, monkeypatch):
    m, w, source, roots, skill = setup(tmp_path)
    monkeypatch.setattr(m, "_copy_payload", lambda *args: (_ for _ in ()).throw(OSError("failed")))
    install(m, w, roots, skill)
    (source / "SKILL.md").write_text("---\nname: s\ndescription: synthetic\n---\n")
    manifest = w / "manifest.json"
    manifest.write_text(json.dumps(dict(manifest_version="test", targets={"user":dict(enabled=True, scope="user", install_path=str(roots))}, skills=[dict(id="s", path="corpus/s")])))
    lines, attention = m.materialize(w, manifest, w / "output", check=True, dry_run=False)
    assert attention and any("PENDING ACTIVE_RECORD" in line for line in lines), lines
    assert not any("ORPHAN_RECORD" in line for line in lines), lines
