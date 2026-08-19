"""Tests for env-driven voter roster resolution."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.metacoordinator_mcp.voters import (
    _CREDENTIAL_ENV_BY_PREFIX,
    _load_builtin_registry,  # noqa: E402
    _parse_weight,
    build_default_voters,
    describe_default_roster,
    make_omo_critic_voter,
    make_executability_voter,
    resolve_default_voter_specs,
)
from packages.orchestrator.claim_schema import (  # noqa: E402
    BlastRadius,
    Claim,
    ProposalType,
)

ENV_KEYS = (
    "ANTHROPIC_API_KEY",
    "CEREBRAS_API_KEY",
    "FLOWITH_API_KEY",
    "FLOWITH_CREDENTIALS_PATH",
    "FLOSS_EXTRA_VOTERS",
    "FLOSS_VOTER_PROFILE",
    "FLOSS_VOTER_ROSTER",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "HF_TOKEN",
    "HUGGINGFACE_API_KEY",
    "MISTRAL_API_KEY",
    "NVIDIA_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "XAI_API_KEY",
)


@contextmanager
def patched_env(**updates: str | None):
    """Temporarily replace the environment variables used by voter resolution."""
    snapshot = {key: os.environ.get(key) for key in ENV_KEYS}
    try:
        for key in ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in updates.items():
            if value is not None:
                os.environ[key] = value
        yield
    finally:
        for key in ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in snapshot.items():
            if value is not None:
                os.environ[key] = value


def test_resolve_default_voter_specs_filters_missing_provider_keys():
    """Return an empty roster when no provider credentials are available."""
    with patched_env():
        resolved = resolve_default_voter_specs(profile="balanced")
    assert resolved == {}


def test_parse_weight_accepts_leading_dot_float():
    """Parse weights like `.8` and `-.4` instead of silently zeroing them out."""
    assert _parse_weight("WEIGHT: .8\nRATIONALE: yes") == 0.8
    assert _parse_weight("WEIGHT: -.4\nRATIONALE: no") == -0.4


def _assert_persona_system_keeps_shared_checklist_mandatory(factory):
    """Exercise a persona wrapper and inspect its higher-priority system contract.

    Patches `_model_completion` — this repo's own backend seam — rather than
    injecting a fake `litellm` into sys.modules. The persona voters route through
    _model_completion so they can reach either litellm or OmniRoute (ADR-19 makes
    OmniRoute the live default), and a sys.modules-level fake does not survive the
    builtins.__import__ substitution that test_server_bootstrap.py performs. That
    made this assertion pass alone and fail after those tests ran. Patching the
    seam we actually own is both order-independent and backend-agnostic.
    """
    from packages.metacoordinator_mcp import voters as voters_module

    completion = Mock(return_value="WEIGHT: -0.4\nRATIONALE: Evidence is missing.")
    voter = factory("persona-probe", "test/model")
    claim = Claim(
        proposer="unit-test",
        proposal_type=ProposalType.CODE_CHANGE,
        summary="missing evidence",
        body="body",
        blast_radius=BlastRadius.LOCAL,
        evidence=[],
    )

    with patch.object(voters_module, "_model_completion", completion):
        voter(claim)

    messages = completion.call_args.args[1]
    assert [message["role"] for message in messages] == ["system", "user"]
    system_message = messages[0]["content"]
    user_message = messages[1]["content"]
    assert "shared seven-item checklist is mandatory" in system_message
    assert (
        "If ANY shared checklist item fails, your weight must not be positive"
        in system_message
    )
    assert "Only after every shared checklist item passes" in system_message
    assert "Run this checklist BEFORE choosing a weight" in user_message
    assert (
        "If ANY checklist item fails, your weight must not be positive" in user_message
    )


def test_omo_critic_system_keeps_shared_checklist_mandatory():
    """The critic lens must not override the shared gate."""
    _assert_persona_system_keeps_shared_checklist_mandatory(make_omo_critic_voter)


def test_executability_reviewer_system_keeps_shared_checklist_mandatory():
    """The executability reviewer's narrow lens must not override the shared gate.

    Renamed with the persona in the 2026-08-12 clean-room rewrite that removed
    SUL-1.0-derived text (ADR-7). Exercises the current factory rather than the
    `make_omo_momus_voter` back-compat alias.
    """
    _assert_persona_system_keeps_shared_checklist_mandatory(make_executability_voter)


def test_resolve_default_voter_specs_honors_profile_and_credentials():
    """Enable only the models backed by credentials for the selected profile."""
    with patched_env(GROQ_API_KEY="test-groq-key"):
        resolved = resolve_default_voter_specs(profile="fast")
    assert resolved == {
        "groq-gpt-oss-20b": "groq/openai/gpt-oss-20b",
    }


def test_roster_override_takes_precedence_over_profile_and_extra():
    """Prefer an explicit roster override over profile and extra voter settings."""
    with patched_env(
        GROQ_API_KEY="test-groq-key",
        FLOSS_VOTER_PROFILE="fast",
        FLOSS_EXTRA_VOTERS="bonus=gemini/custom-model",
        FLOSS_VOTER_ROSTER="solo=groq/openai/gpt-oss-20b",
    ):
        resolved = resolve_default_voter_specs()
    assert resolved == {"solo": "groq/openai/gpt-oss-20b"}


def test_describe_default_roster_marks_missing_credentials_disabled():
    """Mark roster entries disabled when their provider credentials are absent."""
    with patched_env(
        GROQ_API_KEY="test-groq-key",
        FLOSS_EXTRA_VOTERS="gemini-flash=gemini/custom-model",
    ):
        described = describe_default_roster(profile="fast")
    try:
        gemini = next(item for item in described if item["name"] == "gemini-flash")
    except StopIteration as exc:
        raise AssertionError("Expected gemini-flash in described roster") from exc
    assert gemini["enabled"] is False
    assert gemini["reason"] == "missing GOOGLE_API_KEY or GEMINI_API_KEY"


def test_build_default_voters_raises_when_no_enabled_roster_exists():
    """Raise a clear error when no enabled voters can be built."""
    with patched_env():
        try:
            build_default_voters(profile="balanced")
        except RuntimeError as exc:
            assert "No enabled voters" in str(exc)
        else:
            raise AssertionError(
                "Expected RuntimeError when no provider keys are loaded"
            )


def test_flowith_profile_is_removed_after_endpoint_probe():
    """Flowith must stay out of the registry: its endpoint is gone (probed 2026-08-18).

    Regression guard for a subtle trap. Flowith voters never route through
    OmniRoute or litellm -- `build_default_voters` dispatches any `flowith/`
    model to `make_flowith_voter`, a direct HTTPS call to FLOWITH_API_URL
    authenticated from ~/.flowith/credentials.json. Because that credential
    file still exists on disk, `_flowith_credential_state` reports the provider
    as AVAILABLE, so these voters passed the `include_unavailable=False` filter
    and were enrolled into live polls -- while the endpoint itself returned
    404 for every model. Re-adding the profile without first re-probing the
    endpoint would silently reintroduce voters that can only fail at request
    time.
    """
    try:
        resolve_default_voter_specs(profile="flowith")
    except ValueError as exc:
        assert "Unknown voter profile" in str(exc)
    else:
        raise AssertionError(
            "flowith profile is back in voter_registry.json -- re-probe "
            "FLOWITH_API_URL before restoring it"
        )


def test_every_registry_provider_has_a_credential_gate():
    """No profile may reference a provider missing from _CREDENTIAL_ENV_BY_PREFIX.

    A provider absent from that table falls through to "no built-in credential
    gate for provider" and is therefore reported available unconditionally, so
    its voters survive the `include_unavailable=False` filter and join a live
    poll that can only fail at request time. That is exactly how the removed
    flowith voters behaved. `ollama/` is exempt: a local ollama server needs no
    credential, and the `local` profile is documented as requiring
    FLOSS_MODEL_BACKEND=litellm.
    """
    _, profiles = _load_builtin_registry()
    gated = {prefix for prefix, _ in _CREDENTIAL_ENV_BY_PREFIX} | {"ollama/"}
    ungated = {
        model
        for roster in profiles.values()
        for model in roster.values()
        if not any(model.lower().startswith(prefix) for prefix in gated)
    }
    assert not ungated, f"registry models with no credential gate: {sorted(ungated)}"


def test_profile_alias_resolves_to_underlying_registry_profile():
    """Resolve profile aliases to the registry profile they point at.

    `subscriptions` used to alias the flowith roster; that profile was removed
    after its endpoint was probed dead, so the alias now points at `diverse`.
    """
    with patched_env(
        GROQ_API_KEY="test-groq-key",
        MISTRAL_API_KEY="test-mistral-key",
        HUGGINGFACE_API_KEY="test-hf-key",
        NVIDIA_NIM_API_KEY="test-nvidia-key",
        OPENROUTER_API_KEY="test-openrouter-key",
    ):
        by_alias = resolve_default_voter_specs(profile="subscriptions")
        by_name = resolve_default_voter_specs(profile="diverse")
    assert by_alias == by_name
    assert by_alias  # alias must resolve to a non-empty roster


def test_heartbeat_alias_uses_budget_safe_balanced_profile():
    """Routine heartbeat profile must not expand to diverse-max by alias."""
    with patched_env(
        GROQ_API_KEY="test-groq-key",
        MISTRAL_API_KEY="test-mistral-key",
        HUGGINGFACE_API_KEY="test-hf-key",
        NVIDIA_NIM_API_KEY="test-nvidia-key",
    ):
        resolved = resolve_default_voter_specs(profile="heartbeat")
    assert resolved == {
        "groq-gpt-oss-120b": "groq/openai/gpt-oss-120b",
        "mistral-devstral-small": "mistral/devstral-small-latest",
        "huggingface-deepseek-v4-flash": "huggingface/deepseek-ai/DeepSeek-V4-Flash",
        "nvidia-nemotron-super-49b": "nvidia/nvidia/llama-3.3-nemotron-super-49b-v1",
    }


def test_mistral_profile_enables_when_api_key_is_present():
    """Enable the Mistral free roster when its API key is available."""
    with patched_env(MISTRAL_API_KEY="test-mistral-key"):
        resolved = resolve_default_voter_specs(profile="mistral-free")
    assert resolved == {
        "mistral-open-nemo": "mistral/open-mistral-nemo",
        "mistral-ministral-8b": "mistral/ministral-8b-2410",
        "mistral-devstral-small": "mistral/devstral-small-latest",
    }


def test_diverse_profile_prefers_live_cross_provider_roster_when_credentials_exist():
    """Prefer the live multi-provider ROI roster when credentials exist."""
    with patched_env(
        GROQ_API_KEY="test-groq-key",
        MISTRAL_API_KEY="test-mistral-key",
        HUGGINGFACE_API_KEY="test-hf-key",
        NVIDIA_NIM_API_KEY="test-nvidia-key",
        OPENROUTER_API_KEY="test-openrouter-key",
    ):
        resolved = resolve_default_voter_specs(profile="roi")
    assert resolved == {
        "groq-gpt-oss-120b": "groq/openai/gpt-oss-120b",
        "groq-qwen3-27b": "groq/qwen/qwen3.6-27b",
        "mistral-devstral-small": "mistral/devstral-small-latest",
        "huggingface-deepseek-v4-flash": "huggingface/deepseek-ai/DeepSeek-V4-Flash",
        "nvidia-nemotron-super-49b": "nvidia/nvidia/llama-3.3-nemotron-super-49b-v1",
        "openrouter-gpt-4o-mini": "openrouter/openai/gpt-4o-mini",
    }


def test_diverse_plus_profile_adds_optional_openrouter_lane_when_available():
    """Add the optional OpenRouter lane when the wider ROI roster can use it."""
    with patched_env(
        GROQ_API_KEY="test-groq-key",
        MISTRAL_API_KEY="test-mistral-key",
        HUGGINGFACE_API_KEY="test-hf-key",
        NVIDIA_NIM_API_KEY="test-nvidia-key",
        OPENROUTER_API_KEY="test-openrouter-key",
    ):
        resolved = resolve_default_voter_specs(profile="roi-plus")
    assert resolved == {
        "groq-gpt-oss-120b": "groq/openai/gpt-oss-120b",
        "groq-gpt-oss-20b": "groq/openai/gpt-oss-20b",
        "groq-qwen3-27b": "groq/qwen/qwen3.6-27b",
        "mistral-devstral-small": "mistral/devstral-small-latest",
        "mistral-large": "mistral/mistral-large-latest",
        "huggingface-deepseek-v4-flash": "huggingface/deepseek-ai/DeepSeek-V4-Flash",
        "nvidia-nemotron-super-49b": "nvidia/nvidia/llama-3.3-nemotron-super-49b-v1",
        "openrouter-gpt-4o-mini": "openrouter/openai/gpt-4o-mini",
    }


def _run_all() -> int:
    """Run the standalone test module without requiring pytest."""
    tests = [
        test_parse_weight_accepts_leading_dot_float,
        test_omo_critic_system_keeps_shared_checklist_mandatory,
        test_omo_momus_system_keeps_shared_checklist_mandatory,
        test_resolve_default_voter_specs_filters_missing_provider_keys,
        test_resolve_default_voter_specs_honors_profile_and_credentials,
        test_roster_override_takes_precedence_over_profile_and_extra,
        test_describe_default_roster_marks_missing_credentials_disabled,
        test_build_default_voters_raises_when_no_enabled_roster_exists,
        test_flowith_profile_is_removed_after_endpoint_probe,
        test_every_registry_provider_has_a_credential_gate,
        test_profile_alias_resolves_to_underlying_registry_profile,
        test_heartbeat_alias_uses_budget_safe_balanced_profile,
        test_mistral_profile_enables_when_api_key_is_present,
        test_diverse_profile_prefers_live_cross_provider_roster_when_credentials_exist,
        test_diverse_plus_profile_adds_optional_openrouter_lane_when_available,
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {test.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(_run_all())
