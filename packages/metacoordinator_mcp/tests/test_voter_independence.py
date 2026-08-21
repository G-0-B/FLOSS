"""Enforce the voter registry's own independence rule.

Work board row 0.6: "independence is policy, not enforcement". The registry
states a rule -- nontrivial polls need >=3 provider surfaces and >=4 model
families, and same-family endpoints on different surfaces do not count as
independent -- and nothing checked it. PR41 review then found two profiles
governed by that rule sitting below its bar:

  reuse-review  3 surfaces / 3 families  (ADR-18 reuse decisions are nontrivial)
  yumeichan     3 surfaces / 3 families

Both had been voting normally. The failure mode this guards against is the one
the registry itself records: the default `balanced` profile once degraded to two
voters *both on groq* after cerebras died, silently failing its own bar while
continuing to return confident consensus.

Profiles deliberately below the bar must say so in EXEMPT_PROFILES with a
reason. An exemption is a decision someone made on purpose; silence is not.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "voter_registry.json"

MIN_SURFACES = 3
MIN_FAMILIES = 4

# Profiles that are intentionally narrow. Each needs a reason, because the whole
# point of this test is that being under the bar has to be a stated choice.
EXEMPT_PROFILES = {
    "fast": "Latency-first smoke path; explicitly not for nontrivial decisions.",
    "mistral": "Single-vendor probe profile, used to test one surface in isolation.",
    "local": "Offline/no-network fallback -- one local Ollama model is all there is.",
}


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def model_index(registry) -> dict:
    index = registry["_probe"]["verified_working"]
    assert all(isinstance(v, dict) for v in index.values()), (
        "verified_working must be structured objects, not free text -- the rule "
        "cannot be enforced against prose"
    )
    return index


def test_every_profile_model_is_a_probed_model(registry, model_index):
    """A profile must not reference a model nobody confirmed answers.

    Exempt profiles are excluded because they may be probed by another route.
    `local` names ollama/gemma3:12b-it-qat, which is healthy but was confirmed
    directly against localhost:11434 rather than through OmniRoute -- see
    `_probe.local_profile_note`. Pointing it at a hosted model to make a check
    pass would make the profile name a lie, which the registry says explicitly.
    """
    unknown = {
        (profile, model)
        for profile, entries in registry["profiles"].items()
        if profile not in EXEMPT_PROFILES
        for model in entries.values()
        if model not in model_index
    }
    assert not unknown, f"profiles reference unprobed models: {sorted(unknown)}"


def test_local_profile_note_still_explains_its_unprobed_model(registry, model_index):
    """If `local` stops being the documented exception, stop exempting it."""
    local_models = list(registry["profiles"]["local"].values())
    if all(m in model_index for m in local_models):
        pytest.skip("local profile now uses probed models; exemption can be revisited")
    note = registry["_probe"].get("local_profile_note", "")
    assert note.strip(), (
        "the local profile names an unprobed model and no longer says why"
    )


@pytest.mark.parametrize("profile_name", sorted(EXEMPT_PROFILES))
def test_exempt_profiles_are_still_declared_in_the_registry(profile_name, registry):
    """An exemption for a profile that no longer exists is stale bookkeeping."""
    assert profile_name in registry["profiles"], (
        f"{profile_name!r} is exempted here but absent from the registry"
    )


def test_nontrivial_profiles_meet_the_independence_rule(registry, model_index):
    violations = []
    for profile_name, entries in registry["profiles"].items():
        if profile_name in EXEMPT_PROFILES:
            continue
        models = list(entries.values())
        families = {model_index[m]["family"] for m in models if m in model_index}
        surfaces = {model_index[m]["surface"] for m in models if m in model_index}
        if len(surfaces) < MIN_SURFACES or len(families) < MIN_FAMILIES:
            violations.append(
                f"{profile_name}: {len(surfaces)} surface(s) "
                f"{sorted(surfaces)}, {len(families)} family/families "
                f"{sorted(families)}"
            )

    assert not violations, (
        "profiles below the registry's own independence_rule "
        f"(>= {MIN_SURFACES} surfaces, >= {MIN_FAMILIES} families):\n  "
        + "\n  ".join(violations)
        + "\n\nEither widen the profile or add it to EXEMPT_PROFILES with a reason."
    )


def test_same_family_on_two_surfaces_does_not_count_as_independent(model_index):
    """The rule's own worked example must hold in the data.

    groq/qwen/qwen3.6-27b and huggingface/Qwen/Qwen3.6-27B are two surfaces but
    one family. If they ever get recorded as different families, the counting
    above silently becomes permissive.
    """
    groq_qwen = model_index.get("groq/qwen/qwen3.6-27b")
    hf_qwen = model_index.get("huggingface/Qwen/Qwen3.6-27B")
    if groq_qwen is None or hf_qwen is None:
        pytest.skip("the worked-example models are no longer in the registry")

    assert groq_qwen["family"] == hf_qwen["family"]
    assert groq_qwen["surface"] != hf_qwen["surface"]
