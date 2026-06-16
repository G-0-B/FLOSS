"""Tests for env-driven voter roster resolution."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.metacoordinator_mcp.voters import (  # noqa: E402
    _parse_weight,
    build_default_voters,
    describe_default_roster,
    resolve_default_voter_specs,
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
    "MISTRAL_API_KEY",
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


def test_flowith_profile_enables_when_api_key_is_present():
    """Enable the Flowith roster when the API key is present."""
    with patched_env(
        FLOWITH_API_KEY="flo-test-key",
        FLOWITH_CREDENTIALS_PATH="C:/definitely/missing/flowith.json",
    ):
        resolved = resolve_default_voter_specs(profile="flowith")
    assert resolved == {
        "flowith-gpt-4.1-mini": "flowith/gpt-4.1-mini",
        "flowith-gemini-2.5-flash": "flowith/gemini-2.5-flash",
        "flowith-deepseek-chat": "flowith/deepseek-chat",
    }


def test_flowith_profile_reports_missing_credentials_cleanly():
    """Report missing Flowith credentials without crashing roster description."""
    with patched_env(FLOWITH_CREDENTIALS_PATH="C:/definitely/missing/flowith.json"):
        described = describe_default_roster(profile="flowith")
    first = described[0]
    assert first["enabled"] is False
    assert "FLOWITH_API_KEY" in str(first["reason"])


def test_profile_alias_resolves_to_underlying_registry_profile():
    """Resolve profile aliases to the registry profile they point at."""
    with patched_env(
        FLOWITH_API_KEY="flo-test-key",
        FLOWITH_CREDENTIALS_PATH="C:/definitely/missing/flowith.json",
    ):
        resolved = resolve_default_voter_specs(profile="subscriptions")
    assert resolved == {
        "flowith-gpt-4.1-mini": "flowith/gpt-4.1-mini",
        "flowith-gemini-2.5-flash": "flowith/gemini-2.5-flash",
        "flowith-deepseek-chat": "flowith/deepseek-chat",
    }


def test_heartbeat_alias_uses_budget_safe_balanced_profile():
    """Routine heartbeat profile must not expand to diverse-max by alias."""
    with patched_env(
        CEREBRAS_API_KEY="test-cerebras-key",
        GROQ_API_KEY="test-groq-key",
    ):
        resolved = resolve_default_voter_specs(profile="heartbeat")
    assert resolved == {
        "cerebras-llama3.1-8b": "cerebras/llama3.1-8b",
        "groq-gpt-oss-20b": "groq/openai/gpt-oss-20b",
        "groq-qwen3-32b": "groq/qwen/qwen3-32b",
    }


def test_mistral_profile_enables_when_api_key_is_present():
    """Enable the Mistral free roster when its API key is available."""
    with patched_env(MISTRAL_API_KEY="test-mistral-key"):
        resolved = resolve_default_voter_specs(profile="mistral-free")
    assert resolved == {
        "mistral-open-nemo": "mistral/open-mistral-nemo",
        "mistral-ministral-8b": "mistral/ministral-8b-2410",
        "mistral-devstral-small": "mistral/devstral-small-2507",
    }


def test_diverse_profile_prefers_live_cross_provider_roster_when_credentials_exist():
    """Prefer the live multi-provider ROI roster when credentials exist."""
    with patched_env(
        CEREBRAS_API_KEY="test-cerebras-key",
        GROQ_API_KEY="test-groq-key",
        MISTRAL_API_KEY="test-mistral-key",
        FLOWITH_API_KEY="flo-test-key",
        FLOWITH_CREDENTIALS_PATH="C:/definitely/missing/flowith.json",
    ):
        resolved = resolve_default_voter_specs(profile="roi")
    assert resolved == {
        "cerebras-llama3.1-8b": "cerebras/llama3.1-8b",
        "groq-gpt-oss-20b": "groq/openai/gpt-oss-20b",
        "groq-qwen3-32b": "groq/qwen/qwen3-32b",
        "mistral-devstral-small": "mistral/devstral-small-2507",
        "flowith-gemini-2.5-flash": "flowith/gemini-2.5-flash",
        "flowith-deepseek-chat": "flowith/deepseek-chat",
    }


def test_diverse_plus_profile_adds_optional_openai_lane_when_available():
    """Add the optional OpenAI lane when the wider ROI roster can use it."""
    with patched_env(
        CEREBRAS_API_KEY="test-cerebras-key",
        GROQ_API_KEY="test-groq-key",
        MISTRAL_API_KEY="test-mistral-key",
        FLOWITH_API_KEY="flo-test-key",
        FLOWITH_CREDENTIALS_PATH="C:/definitely/missing/flowith.json",
        OPENAI_API_KEY="test-openai-key",
    ):
        resolved = resolve_default_voter_specs(profile="roi-plus")
    assert resolved == {
        "cerebras-llama3.1-8b": "cerebras/llama3.1-8b",
        "groq-gpt-oss-20b": "groq/openai/gpt-oss-20b",
        "groq-qwen3-32b": "groq/qwen/qwen3-32b",
        "mistral-devstral-small": "mistral/devstral-small-2507",
        "flowith-gemini-2.5-flash": "flowith/gemini-2.5-flash",
        "flowith-deepseek-chat": "flowith/deepseek-chat",
        "openai-gpt-4.1-mini": "openai/gpt-4.1-mini",
    }


def _run_all() -> int:
    """Run the standalone test module without requiring pytest."""
    tests = [
        test_parse_weight_accepts_leading_dot_float,
        test_resolve_default_voter_specs_filters_missing_provider_keys,
        test_resolve_default_voter_specs_honors_profile_and_credentials,
        test_roster_override_takes_precedence_over_profile_and_extra,
        test_describe_default_roster_marks_missing_credentials_disabled,
        test_build_default_voters_raises_when_no_enabled_roster_exists,
        test_flowith_profile_enables_when_api_key_is_present,
        test_flowith_profile_reports_missing_credentials_cleanly,
        test_profile_alias_resolves_to_underlying_registry_profile,
        test_heartbeat_alias_uses_budget_safe_balanced_profile,
        test_mistral_profile_enables_when_api_key_is_present,
        test_diverse_profile_prefers_live_cross_provider_roster_when_credentials_exist,
        test_diverse_plus_profile_adds_optional_openai_lane_when_available,
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
