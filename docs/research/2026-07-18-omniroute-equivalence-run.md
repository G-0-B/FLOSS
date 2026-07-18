# OmniRoute Equivalence Run — Stage 3.5 Results

**Date:** 2026-07-18
**Truth Status:** [V] Verified (litellm baseline); [S] Specified (OmniRoute — blocked on provider config)

## Litellm Baseline ✅ PASS

```
FLOSS_MODEL_BACKEND=litellm python scripts/smoke_test_voters.py
```

- 3/3 voters returned parseable WEIGHT/RATIONALE output
- All voters functional (groq-gpt-oss-20b, groq-qwen3-32b, cerebras-gpt-oss-120b)
- Consensus round completed in 9169ms
- Outcome: REJECTED (expected — smoke test claim has no evidence)
- **Key criterion met: all voters parseable, no errors, consensus gate is LIVE**

## OmniRoute Equivalence ⚠️ BLOCKED (Task 3.2 gate)

OmniRoute daemon started successfully (v3.8.45, `http://127.0.0.1:20128/v1`).
However, the existing voter roster model IDs (`groq/openai/gpt-oss-20b`, `cerebras/gpt-oss-120b`, etc.)
do not resolve through OmniRoute — it uses its own model namespace (`auto/best-fast`, `ddgw/gpt-4o-mini`, `tllm/GPT_5`, etc.).

OmniRoute loaded the FLOSS `.env` (with GROQ_API_KEY, CEREBRAS_API_KEY, MISTRAL_API_KEY)
but does not automatically register providers from env vars. Providers must be configured
through OmniRoute's dashboard at `http://localhost:20128`.

**Error:** `"No active credentials for provider: groq"` when calling with `groq/openai/gpt-oss-20b`

## What's needed to complete the equivalence run

1. **Configure providers in OmniRoute dashboard** — add Groq, Cerebras, Mistral API keys through the OmniRoute UI/API
2. **Build model-ID mapping** — map litellm-style IDs to OmniRoute model IDs:
   - `groq/openai/gpt-oss-20b` → OmniRoute equivalent
   - `cerebras/gpt-oss-120b` → OmniRoute equivalent
   - `groq/qwen/qwen3.6-27b` → OmniRoute equivalent
3. **Re-run smoke_test_voters.py** with `FLOSS_MODEL_BACKEND=omniroute` and mapped IDs
4. **Verify** all voters return parseable WEIGHT/RATIONALE output

## Current state

- `FLOSS_MODEL_BACKEND` defaults to `litellm` (unchanged — correct per plan)
- All infrastructure is in place: OmniRoute client, flag-gated routing, daemon bootstrap
- The switch to OmniRoute is **gated on provider configuration + model mapping**, not on code
- This is exactly the Task 3.2 gate the plan anticipated: *"any that don't → keep on litellm via the flag"*

## Decision

Keep `FLOSS_MODEL_BACKEND=litellm` as default. The OmniRoute path is implemented, tested (3/3 TDD),
and ready — but requires provider configuration through OmniRoute's dashboard before it can be
used with the existing voter roster. This is a configuration task for Anthony, not a code change.
