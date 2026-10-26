"""Behavioral qualification of the three independent C03 residuals."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path

import pytest
from packages.preservation_spine import cli, seal
from packages.preservation_spine.github_projection import render_check_summary
from packages.preservation_spine.models import ResultStatus, canonical_json_bytes
from packages.preservation_spine.tests.test_github_projection import _evidence, _verification


def write_record(tmp_path, content):
    capsule = tmp_path / "capsule"
    capsule.mkdir()
    path = capsule / "verification.json"
    path.write_bytes(content)
    return path


def test_canonical_verification_round_trip(tmp_path):
    record = _verification()
    content = canonical_json_bytes(record)
    path = write_record(tmp_path, content)
    assert cli._load_verification(tmp_path) == record
    assert path.read_bytes() == content


@pytest.mark.parametrize("mutation", ["pretty", "reordered", "duplicate-top", "duplicate-plane", "coerced-type", "missing-default"])
def test_verification_rejects_noncanonical_bytes(tmp_path, mutation):
    content = canonical_json_bytes(_verification())
    data = json.loads(content)
    if mutation == "pretty":
        content = json.dumps(data, indent=2).encode()
    elif mutation == "reordered":
        content = json.dumps(dict(reversed(list(data.items()))), separators=(",", ":")).encode() + b"\n"
    elif mutation == "duplicate-top":
        content = content.replace(b'"schema_version":"1"', b'"schema_version":"unbound","schema_version":"1"', 1)
    elif mutation == "duplicate-plane":
        content = content.replace(b'"tree_id":', b'"tree_id":"unbound","tree_id":', 1)
    elif mutation == "coerced-type":
        data["schema_version"] = 1
        content = canonical_json_bytes(data)
    elif mutation == "missing-default":
        del data["planes"][0]["parent_match"]
        content = canonical_json_bytes(data)
    path = write_record(tmp_path, content)
    with pytest.raises(ValueError):
        cli._load_verification(tmp_path)
    assert path.read_bytes() == content


@pytest.mark.parametrize("location", ["top", "plane"])
def test_unknown_field_guard_survives(tmp_path, location):
    data = json.loads(canonical_json_bytes(_verification()))
    target = data if location == "top" else data["planes"][0]
    target["extra_unbound"] = "C03"
    write_record(tmp_path, canonical_json_bytes(data))
    with pytest.raises(ValueError, match="unbound|malformed"):
        cli._load_verification(tmp_path)


@pytest.mark.parametrize("content", [b"{", b"[]", b"\xff"])
def test_malformed_record_rejected(tmp_path, content):
    write_record(tmp_path, content)
    with pytest.raises((ValueError, UnicodeDecodeError)):
        cli._load_verification(tmp_path)


def test_digest_helper_keeps_reverification_behavior(tmp_path):
    # Deliberately do not adopt PR59's separate recovery contract change.
    path = write_record(tmp_path, b"noncanonical bytes")
    assert cli._verification_digest(path) == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("status", [ResultStatus.PASS, ResultStatus.BLOCKED, ResultStatus.FAIL])
@pytest.mark.parametrize("bound", [False, True])
def test_unbound_diagnostic_is_independent_of_status(status, bound):
    evidence = _evidence(verification_status=status)
    digest = hashlib.sha256(canonical_json_bytes(evidence.verification)).hexdigest() if bound else None
    checkpoint = replace(evidence.checkpoint, verification_digest=digest, digest=None)
    summary = render_check_summary(replace(evidence, checkpoint=checkpoint))
    assert ("verification-digest-unbound" in summary["blockers"]) is (not bound)
    if not bound:
        assert summary["preservation"]["status"] != ResultStatus.PASS.value


def test_fixed_output_fdopen_failure_closes_descriptor_and_preserves_evidence(tmp_path, monkeypatch):
    output = tmp_path / "verification.json"
    output.write_bytes(b"previous output")
    captured = []
    replacements = []

    def fail_open(fd, *args, **kwargs):
        captured.append(fd)
        raise OSError("C03 injected fdopen failure")

    def unexpected_replace(*args):
        replacements.append(args)
        raise AssertionError("must not publish after fdopen failure")

    monkeypatch.setattr(seal.os, "fdopen", fail_open)
    monkeypatch.setattr(seal.os, "replace", unexpected_replace)
    failure = None
    try:
        seal._atomic_write_fixed(tmp_path, "verification.json", b"new output")
    except Exception as exc:
        failure = exc
    assert len(captured) == 1
    try:
        os.fstat(captured[0])
        closed = False
    except OSError:
        closed = True
    finally:
        if not locals().get("closed", True):
            os.close(captured[0])  # fixture hygiene; record leak before closing
    assert output.read_bytes() == b"previous output"
    assert len(list(tmp_path.glob(".verification.json.pending-*"))) == 1
    assert not replacements
    assert closed, "raw descriptor leaked after fdopen failure"
    assert isinstance(failure, seal.CapsuleVerificationError)


def test_fixed_output_success(tmp_path):
    seal._atomic_write_fixed(tmp_path, "verification.json", b"new output")
    assert (tmp_path / "verification.json").read_bytes() == b"new output"


def test_retained_identity_guard_survives(tmp_path):
    capsule, other = tmp_path / "capsule", tmp_path / "other"
    capsule.mkdir()
    other.mkdir()
    with pytest.raises(seal.CapsuleVerificationError, match="retained identity"):
        seal._atomic_write_fixed(capsule, "verification.json", b"new", retained_identity=seal._validated_directory_state(other))
    assert not list(capsule.iterdir())
