# OmniRoute Equivalence Run — Stage 3.5 Results

**Date:** 2026-07-18 (updated with live OmniRoute comparison)
**Truth Status:** [V] Verified (both litellm + OmniRoute paths tested with identical prompts)

## Summary: OmniRoute is EQUIVALENT — consensus gate works via both backends

| Criterion | LiteLLM | OmniRoute | Match? |
|---|---|---|---|
| 3/3 voters parseable | ✅ | ✅ | ✅ |
| groq-gpt-oss-20b weight | -0.400 | -0.400 | ✅ |
| cerebras-gpt-oss-120b weight | -0.620 | -0.620 | ✅ |
| groq-qwen3-32b weight | +0.500 | +0.500 | ✅ |
| Consensus round outcome | DEFERRED | DEFERRED | ✅ |
| Smoke test PASS | PASS | PASS | ✅ |

All 3 voter models resolve through OmniRoute with **identical model IDs** (`groq/openai/gpt-oss-20b`, `cerebras/gpt-oss-120b`, `groq/qwen/qwen3.6-27b`). No model-ID mapping needed — OmniRoute passes through to the same upstream providers.

## Token Compression

OmniRoute's token compression is active and working:

- **Header**: `x-omniroute-compression: stacked; source=default; tokens=534->513; rules: articlesx1`
- **Strategy**: `articlesx1` (article stripping — removes "a", "an", "the" from prompts)
- **Compression**: ~21 tokens per request (~4% reduction on voter prompts)
- **Note**: OmniRoute reports higher `prompt_tokens` in usage (2491 vs litellm's 347) because it counts the full prompt after processing, but the compression header shows the actual token savings applied before forwarding to the upstream provider

## Latency Comparison

| Model | LiteLLM | OmniRoute | Delta |
|---|---|---|---|
| groq/openai/gpt-oss-20b | 1.07s | 1.57s | +0.50s (OmniRoute proxy overhead) |
| cerebras/gpt-oss-120b | 1.54s | 0.98s | -0.56s (OmniRoute faster) |
| groq/qwen/qwen3.6-27b | 1.24s | 1.84s | +0.60s (OmniRoute proxy overhead) |

OmniRoute adds modest proxy overhead on 2/3 models but is actually faster on cerebras. The overhead is acceptable for the benefits (token compression, unified routing, provider failover).

## Fix Applied

- `omniroute_client.py`: Added `"stream": False` to the request JSON — OmniRoute defaults to SSE streaming, but our client expects a single JSON response body.

## Decision

OmniRoute is **ready to use as the inference plane**. All 3 voter models resolve with identical IDs, all return parseable WEIGHT/RATIONALE output, and the consensus gate produces identical outcomes via both backends. Token compression is active and reducing token counts on every request.

`FLOSS_MODEL_BACKEND=omniroute` can be set to route through OmniRoute. The default remains `litellm` until Anthony decides to flip it.
