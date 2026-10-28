"""Qualify generated-node type parity without invoking live materialization."""

import importlib.util
import os
from pathlib import Path
import subprocess

import pytest


@pytest.fixture
def module():
    path = Path(
        os.environ.get(
            "C04_MATERIALIZER_PATH",
            Path(__file__).resolve().parents[2]
            / "scripts/materialize_shared_skill_surface.py",
        )
    )
    spec = importlib.util.spec_from_file_location("c04_filter_under_test", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.mark.parametrize(
    "name",
    ["desktop.ini", ".DS_Store", "Thumbs.db", "asset.pyc", "asset.pyo", "__pycache__"],
)
@pytest.mark.parametrize("directory", [False, True])
def test_generated_looking_names_are_classified_by_node_type(
    module, tmp_path, name, directory
):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    (source / "control.bin").write_bytes(b"\0\xffC04\r\n")
    node = source / name
    if directory:
        node.mkdir()
        (node / "lesson.bin").write_bytes(b"\xffindependent payload\0")
        included = name != "__pycache__"
        payload_path = name + "/lesson.bin"
    else:
        node.write_bytes(b"\xffregular file payload\0")
        included = name == "__pycache__"
        payload_path = name
    expected = {"control.bin"} | ({payload_path} if included else set())
    assert set(module.payload_digests(source)) == expected
    module._copy_payload(source, target)
    assert set(module.payload_digests(target)) == expected
    assert module.payload_digests(target) == module.payload_digests(source)
    if included:
        assert (target / payload_path).read_bytes() == (
            source / payload_path
        ).read_bytes()
    else:
        assert not (target / name).exists()
        assert not (target / name).is_symlink()
    assert (target / "control.bin").read_bytes() == b"\0\xffC04\r\n"


def test_nested_directory_payload_and_generated_cache_controls(module, tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    (source / "nested" / "desktop.ini").mkdir(parents=True)
    (source / "nested" / "desktop.ini" / "lesson.md").write_bytes(b"kept\r\n")
    (source / "nested" / "desktop.ini" / "desktop.ini").write_bytes(b"shell metadata")
    (source / "nested" / "__pycache__").mkdir()
    (source / "nested" / "__pycache__" / "cache.bin").write_bytes(b"\xff")
    (source / "nested" / "generated.pyc").write_bytes(b"\xff")
    module._copy_payload(source, target)
    assert set(module.payload_digests(source)) == {"nested/desktop.ini/lesson.md"}
    assert module.payload_digests(target) == module.payload_digests(source)
    assert (target / "nested/desktop.ini/lesson.md").read_bytes() == b"kept\r\n"
    assert not (target / "nested/__pycache__").exists()
    assert not (target / "nested/generated.pyc").exists()
    assert not (target / "nested/desktop.ini/desktop.ini").exists()


def symlink_or_skip(link, target, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError as exc:
        pytest.skip("symlink capability unavailable: " + str(exc))


@pytest.mark.parametrize("name", ["desktop.ini", "asset.pyc", "normal"])
def test_directory_symlink_preserved_as_link(module, tmp_path, name):
    source, target, outside = (
        tmp_path / "source",
        tmp_path / "target",
        tmp_path / "outside",
    )
    source.mkdir()
    outside.mkdir()
    (outside / "outside.bin").write_bytes(b"outside fixture payload")
    symlink_or_skip(source / name, outside, directory=True)
    assert module.payload_digests(source) == {
        name: "link:" + os.readlink(source / name)
    }
    module._copy_payload(source, target)
    assert (target / name).is_symlink()
    assert os.readlink(target / name) == os.readlink(source / name)
    assert module.payload_digests(target) == module.payload_digests(source)


def test_dangling_and_loop_links_are_not_followed(module, tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    symlink_or_skip(source / "dangling", tmp_path / "absent")
    symlink_or_skip(source / "loop-a", source / "loop-b", directory=True)
    symlink_or_skip(source / "loop-b", source / "loop-a", directory=True)
    module._copy_payload(source, target)
    assert set(module.payload_digests(target)) == {"dangling", "loop-a", "loop-b"}
    assert module.payload_digests(target) == module.payload_digests(source)


@pytest.mark.parametrize("name", ["Desktop.ini", "THUMBS.DB", "X.PYC", "__PYCACHE__"])
@pytest.mark.parametrize("directory", [False, True])
def test_case_variants_follow_exact_digest_policy(module, tmp_path, name, directory):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    if directory:
        (source / name).mkdir()
        (source / name / "lesson.bin").write_bytes(b"\xffkept")
        expected = {name + "/lesson.bin"}
    else:
        (source / name).write_bytes(b"\xffkept")
        expected = {name}
    assert set(module.payload_digests(source)) == expected
    module._copy_payload(source, target)
    assert set(module.payload_digests(target)) == expected
    assert (target / name).exists()


def test_generated_directory_symlink_is_physically_excluded(module, tmp_path):
    source, target, outside = (
        tmp_path / "source",
        tmp_path / "target",
        tmp_path / "outside",
    )
    source.mkdir()
    outside.mkdir()
    symlink_or_skip(source / "__pycache__", outside, directory=True)
    module._copy_payload(source, target)
    assert not (target / "__pycache__").exists()
    assert not (target / "__pycache__").is_symlink()


@pytest.mark.parametrize("name", ["desktop.ini", "x.pyc"])
@pytest.mark.parametrize("dangling", [False, True])
def test_generated_file_symlinks_are_physically_excluded(
    module, tmp_path, name, dangling
):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    external = tmp_path / "external.bin"
    if not dangling:
        external.write_bytes(b"fixture payload")
    symlink_or_skip(source / name, external)
    module._copy_payload(source, target)
    assert not (target / name).exists()
    assert not (target / name).is_symlink()


def test_dangling_link_with_generated_directory_name_is_payload(module, tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    symlink_or_skip(source / "__pycache__", tmp_path / "absent")
    assert set(module.payload_digests(source)) == {"__pycache__"}
    module._copy_payload(source, target)
    assert (target / "__pycache__").is_symlink()
    assert module.payload_digests(target) == module.payload_digests(source)


@pytest.mark.skipif(
    os.name != "nt" or not hasattr(os.path, "isjunction"),
    reason="Windows Python3.12+ junction classification",
)
@pytest.mark.parametrize(
    "name", ["desktop.ini", "asset.pyc", "__pycache__", "Desktop.ini", "__PYCACHE__"]
)
def test_junction_legacy_exclusion_is_retained(module, tmp_path, name):
    source, target, outside = (
        tmp_path / "source",
        tmp_path / "target",
        tmp_path / "outside",
    )
    source.mkdir()
    outside.mkdir()
    (outside / "outside.bin").write_bytes(b"fixture-only payload")
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(source / name), str(outside)],
        capture_output=True,
    )
    if result.returncode:
        pytest.skip("junction capability unavailable")
    module._copy_payload(source, target)
    assert not (target / name).exists()
    assert not (target / name).is_junction()
    # Junction parity is deliberately not claimed: excluded legacy junction
    # behavior is retained in these stable fixtures; source type races are unqualified.


@pytest.mark.parametrize("name", ["desktop.ini", "normal.bin"])
def test_classification_error_keeps_legacy_filter_without_new_exception(
    module, tmp_path, monkeypatch, name
):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    (source / name).write_bytes(b"fixture payload")
    original = Path.is_dir

    def cannot_classify(path):
        if path == source / name:
            raise PermissionError("injected classification failure")
        return original(path)

    monkeypatch.setattr(Path, "is_dir", cannot_classify)
    module._copy_payload(source, target)
    assert (target / name).exists() is (name == "normal.bin")


def test_existing_destination_survives_classification_error(
    module, tmp_path, monkeypatch
):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "desktop.ini").write_bytes(b"metadata")
    (target / "foreign.bin").write_bytes(b"independent writer")
    original = Path.is_dir

    def cannot_classify(path):
        if path == source / "desktop.ini":
            raise PermissionError("injected classification failure")
        return original(path)

    monkeypatch.setattr(Path, "is_dir", cannot_classify)
    with pytest.raises(FileExistsError):
        module._copy_payload(source, target)
    assert (target / "foreign.bin").read_bytes() == b"independent writer"


@pytest.mark.skipif(
    os.name != "nt", reason="Windows missing-junction-classifier fallback"
)
def test_missing_junction_classifier_retains_legacy_filter(
    module, tmp_path, monkeypatch
):
    source, target = tmp_path / "source", tmp_path / "target"
    (source / "desktop.ini").mkdir(parents=True)
    (source / "desktop.ini/lesson.bin").write_bytes(b"payload")
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    module._copy_payload(source, target)
    assert not (target / "desktop.ini").exists()
