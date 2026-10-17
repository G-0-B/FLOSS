"""
Unit tests for FLOSS benchmark dataset staging and projection governance.
Verifies native file integrity, provenance manifests, and candidate governance blocks.
Part of Phase 3 (Task 3.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stage_benchmark_datasets import sha256_file, EVALS_DIR


def test_scifact_native_staging_and_manifest():
    scifact_dir = EVALS_DIR / "entailment" / "scifact_native"
    manifest_file = scifact_dir / "manifest.json"
    assert manifest_file.is_file(), f"Missing SciFact manifest at {manifest_file}"

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["dataset"] == "SciFact"
    assert manifest["license"] == "CC-BY-NC-2.0"
    assert "claims_dev.jsonl" in manifest["files"]
    assert "corpus.jsonl" in manifest["files"]

    dev_info = manifest["files"]["claims_dev.jsonl"]
    actual_dev_path = EVALS_DIR / "entailment" / "scifact_native" / "claims_dev.jsonl"
    assert actual_dev_path.is_file()
    assert sha256_file(actual_dev_path) == dev_info["sha256"]
    assert dev_info["record_count"] == 300


def test_redocred_native_staging_and_manifest():
    redocred_dir = EVALS_DIR / "document_relation" / "redocred_native"
    manifest_file = redocred_dir / "manifest.json"
    assert manifest_file.is_file(), f"Missing Re-DocRED manifest at {manifest_file}"

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["dataset"] == "Re-DocRED"
    assert manifest["license"] == "CC-BY-SA-4.0"

    dev_file = redocred_dir / "dev_revised.json"
    assert dev_file.is_file()
    assert sha256_file(dev_file) == manifest["file"]["sha256"]
    assert manifest["file"]["document_count"] == 500


def test_scifact_candidate_projection_governance():
    proj_file = EVALS_DIR / "entailment" / "floss_projection" / "projected_claims_dev.jsonl"
    assert proj_file.is_file(), f"Missing projected SciFact claims at {proj_file}"

    with open(proj_file, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    assert len(lines) >= 10
    for line in lines[:10]:
        rec = json.loads(line)
        assert "claim_id" in rec
        assert "statement" in rec
        assert "projected_stance" in rec
        assert rec["projected_stance"] in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "CONFLICTING")

        # Crucial governance check: MUST NOT claim authoritative gold
        gov = rec.get("governance", {})
        assert gov["mapping_status"] == "candidate"
        assert gov["adjudication_id"] is None
        assert gov["license_snapshot"] == "CC-BY-NC-2.0"
        assert len(gov["upstream_record_hash"]) == 64


def test_redocred_candidate_projection_governance():
    proj_file = EVALS_DIR / "document_relation" / "floss_projection" / "projected_dev.jsonl"
    assert proj_file.is_file(), f"Missing projected Re-DocRED docs at {proj_file}"

    with open(proj_file, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    assert len(lines) >= 5
    for line in lines[:5]:
        rec = json.loads(line)
        assert "document_id" in rec
        assert "relations" in rec
        assert rec["relation_count"] == len(rec["relations"])

        # Crucial governance check
        gov = rec.get("governance", {})
        assert gov["mapping_status"] == "candidate"
        assert gov["adjudication_id"] is None
        assert gov["license_snapshot"] == "CC-BY-SA-4.0"
        assert len(gov["upstream_record_hash"]) == 64
