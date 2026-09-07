---
id: project-omniroute-voter-probe-log
type: project
created: '2026-08-18'
status: active
applies_to:
- any-agent
source: direct_functional_probe_2026_08_18
title: OmniRoute catalog status is unreliable — probe log of what actually answers
---

Direct functional probes through OmniRoute (`omniroute_route_request`) on 2026-08-18,
version 3.8.48. Every model below was listed by `omniroute_list_models_catalog` with
`status: "available"`.

**The headline finding: `status: "available"` in the catalog is a claim, not evidence.**
Most models advertised as available failed on a one-token functional probe. ADR-18's rule
("unprobed incompatibility claims cannot justify `build`") cuts both ways — an unprobed
*availability* claim cannot justify putting a model in a voter roster either.

**Probed WORKING (returned the exact requested token):**

| model | family | surface | latency |
|---|---|---|---|
| `groq/openai/gpt-oss-120b` | OpenAI-oss | Groq | 489 ms |
| `groq/openai/gpt-oss-20b` | OpenAI-oss | Groq | 359 ms |
| `groq/qwen/qwen3.6-27b` | Qwen/Alibaba | Groq | 562 ms |
| `mistral/mistral-large-latest` | Mistral | Mistral | 638 ms |
| `mistral/devstral-small-latest` | Mistral | Mistral | 534 ms |
| `mistral/open-mistral-nemo` | Mistral | Mistral | 407 ms |
| `mistral/ministral-8b-2410` | Mistral | Mistral | 407 ms |
| `huggingface/Qwen/Qwen3.6-27B` | Qwen/Alibaba | HuggingFace | 2 349 ms |
| `huggingface/deepseek-ai/DeepSeek-V4-Flash` | DeepSeek | HuggingFace | 5 785 ms |
| `openrouter/openai/gpt-4o-mini` | GPT-4o | OpenRouter | 1 022 ms |
| `nvidia/openai/gpt-oss-20b` | OpenAI-oss | NVIDIA | 669 ms |
| `nvidia/nvidia/llama-3.3-nemotron-super-49b-v1` | Nemotron | NVIDIA | 448 ms |
| `ollama/gemma3:12b-it-qat` (direct, :11434) | Google/Gemma | local | ~19 s cold |

Five surfaces, six families. Note `ollama` is reachable **only** directly — OmniRoute has no
ollama credential, so it cannot serve as a voter while `FLOSS_MODEL_BACKEND=omniroute`.

**Probed FAILING:**

- `cerebras/gpt-oss-120b` — 404. **In the `balanced`, `fast`, `diverse`, `diverse-max`, and
  `yumeichan` profiles.** The error text names a *different* model (`zai-glm-4.7 is
  archived`) than the one requested, and the "reset after Nm" countdown keeps restarting —
  the error appears cached per-provider rather than per-model. Treat Cerebras as down for
  this org until re-probed.
- `groq/llama-3.3-70b-versatile` — 404, "does not exist or you do not have access".
  **In the `diverse-max` profile.**
- `gemini/gemini-2.5-flash` — 404, deprecated; the API itself suggests `gemini-3.6-flash`.
  `gemini/gemini-3.6-flash` then timed out.
- `cohere/*`, `bluesminds/*` — timeout or 404 on every attempt.
- Bare model IDs are rejected as ambiguous; the `provider/model` prefix is mandatory.

**Corrections made during this same pass — both worth internalizing:**

- **`nvidia/*` is NOT dead.** The first probes used wrong model ids. `nvidia/openai/gpt-oss-20b`
  (669 ms) and `nvidia/nvidia/llama-3.3-nemotron-super-49b-v1` (448 ms) both answer. A 404 on a
  guessed id says nothing about the surface. `openrouter/openai/gpt-4o-mini` (1022 ms) also works.
- **`flowith/*` does not use OmniRoute at all.** `build_default_voters` dispatches by voter-name
  prefix first, then model prefix: any `flowith/` model goes to `make_flowith_voter`, a direct HTTPS
  call to `FLOWITH_API_URL` authenticated from `~/.flowith/credentials.json`. An OmniRoute
  "no active credentials for provider: flowith" result is therefore *irrelevant* to flowith. Probed
  properly, the credential file loads fine but the endpoint returns **404 for every model** — so
  flowith is dead **at that URL**, but for a completely different reason than first recorded.
  **Probe the path the code actually takes, not the path you assume it takes.**
  Operator context (2026-08-18): Flowith is a *separate AI harness* whose tokens, API, and model
  access were harvested into this stack; it keeps its own config under the user folder and AppData.
  Only `~/.flowith/credentials.json` was found (no endpoint config), so the hardcoded
  `FLOWITH_API_URL` in `voters.py` is the sole reference and it 404s. Treat this as **recoverable,
  not permanently dead**: if the current endpoint can be read out of the Flowith harness's own
  config, restoring `FLOWITH_API_URL` brings back a genuinely independent surface (Gemini/DeepSeek
  families) that OmniRoute does not otherwise provide.
- **An ungated provider is worse than a dead one.** `_CREDENTIAL_ENV_BY_PREFIX` had no entry for
  `huggingface/` or `nvidia/`, so `_credential_state_for_model` returned "no built-in credential gate"
  = available unconditionally. Such voters survive the `include_unavailable=False` filter and join a
  live poll that can only fail at request time — exactly how flowith behaved with a stale credential
  file present. Gates for both were added, plus a test asserting every registry provider is gated.

**Repair applied 2026-08-18:** `voter_registry.json` now contains only probed-working models and carries a `_probe` block recording the evidence, the removals with reasons, and a falsifier. Every profile that is meant to be independent now clears the bar (`balanced` 4 surfaces/4 families; `diverse*` 5/6; `reuse-review` 3/3 per ADR-18). `local` deliberately still names ollama and documents that it needs `FLOSS_MODEL_BACKEND=litellm`, rather than being repointed at a hosted model to make the name pass.

**Why this mattered (the state that was found, now repaired):** `balanced` — the DEFAULT
profile — was `groq-gpt-oss-20b` + `groq-qwen3-32b` + `cerebras-gpt-oss-120b`. Once Cerebras
died it degraded to two voters *both on the Groq surface*, i.e. one surface and effectively no
independence, while still reporting a normal consensus outcome. The diversity policy requires
≥3 provider surfaces and ≥4 model families and says same-family endpoints do not count — so
every `balanced` poll silently failed its own bar. ADR-18's `reuse-review` had the same problem
via ollama. **Nothing in the code detected or reported either.** The standing gap is that
independence is still a documented policy, not an enforced check: consider asserting
surface/family counts at roster-build time so a degraded roster fails loudly instead of voting.

**How to apply:** Probe before trusting any roster entry. Prefer the six verified-working
entries above when independence actually matters, choosing across *families* not just
endpoints (`groq/qwen` and `huggingface/Qwen` are the same family and do not add
independence). Re-probe before relying on this log — it is a dated snapshot, not a
standing guarantee, and the failures above may be transient quota/circuit-breaker state.

Related: [[project-omo-momus-voter]], [[project-mcp-orchestrator-roadmap]],
[[feedback-no-unauthorized-modifications]].
