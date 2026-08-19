from __future__ import annotations

from pathlib import Path

import yaml


FLOSS_ROOT = Path(__file__).resolve().parents[2]
ROSE_FOREST = FLOSS_ROOT / "ARF" / "dnas" / "rose_forest"


def test_consent_integrity_zome_is_packaged_in_rose_forest_dna():
    dna_yaml = yaml.safe_load((ROSE_FOREST / "workdir" / "dna.yaml").read_text())

    # hc manifests use `path:` for unbundled zome wasm and `bundled:` for the
    # packed form — support both so the test works against either manifest style.
    integrity_zomes = {
        zome["name"]: zome.get("bundled") or zome.get("path")
        for zome in dna_yaml["integrity"]["zomes"]
    }

    assert "consent_integrity" in integrity_zomes
    assert (
        integrity_zomes["consent_integrity"]
        == "../../../target/wasm32-unknown-unknown/release/consent_integrity.wasm"
    )

    consent_coord = next(
        zome
        for zome in dna_yaml["coordinator"]["zomes"]
        if zome["name"] == "consent"
    )
    assert (
        consent_coord.get("bundled") or consent_coord.get("path")
    ) == "../../../target/wasm32-unknown-unknown/release/consent.wasm"
    dependencies = {dep["name"] for dep in consent_coord["dependencies"]}
    assert "consent_integrity" in dependencies


def test_consent_integrity_crate_is_in_arf_workspace():
    cargo_toml = (FLOSS_ROOT / "ARF" / "Cargo.toml").read_text()

    assert '"dnas/rose_forest/zomes/consent_integrity"' in cargo_toml


def test_consent_coordinator_depends_on_consent_integrity():
    cargo_toml = (
        ROSE_FOREST / "zomes" / "consent_coordinator" / "Cargo.toml"
    ).read_text()

    assert "consent_integrity" in cargo_toml


def test_consent_coordinator_exposes_consent_gate_api():
    lib_rs = (
        ROSE_FOREST / "zomes" / "consent_coordinator" / "src" / "lib.rs"
    ).read_text()

    for function_name in (
        "create_consent_payload",
        "create_consent_decision",
        "get_consent_payload",
        "get_consent_decision",
        "get_consent_decisions_for_payload",
    ):
        assert f"pub fn {function_name}" in lib_rs
