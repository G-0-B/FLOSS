# OmniRoute Compression Tuning

**Date:** 2026-07-26
**Truth Status:** ⚠️ Specified — two settings changed and verified; the measurement pass is not yet run.

## What `maxTokens` actually means

Authoritative, from the `omniroute_compression_configure` tool schema:

> `maxTokens` — "Maximum tokens before compression triggers"

It is a **trigger threshold**, not a context cap. Confirmed a second way: the configure response reports the field it updated as `autoTriggerTokens`. Nothing was ever truncated to 1000 tokens. The operator's original understanding was correct; an earlier reading of this as a context cap was wrong.

## Why it still mattered

`maxTokens: 1000` meant "compress anything over 1000 tokens" — i.e. effectively always.

| Measure | Value (2026-07-26, before change) |
|---|---|
| Requests compressed | 259 / 259 = **100%** |
| Prompt tokens (174 receipted) | 15,611,047 → **~90k avg/request** |
| `auto/best-coding` context window | 1,048,576 |
| Context utilisation | **~9%** |
| Tokens saved | 4,031,817 (~26%), **$4.22** |
| MCP description compression | 59 descriptions, 345 chars, **104 tokens total** |

At 9% utilisation there is no context pressure to relieve. Compression was running on every request, buying nothing operationally, and degrading fidelity. `preserveSystemPrompt: true` protected the system prompt — but **not conversation content and not tool/skill descriptions**, which is the failure surface.

This is a probable contributing factor in the 2026-07-26 incident pair (see agent-memory `confabulated-defect-report`): an agent reasoning over lossily-compressed conversation *and* lossily-compressed skill instructions saved a skill's documentation example as real project knowledge, and separately invented a syntax error to explain a non-zero exit code.

## Applied

```
maxTokens                        1000  ->  131072
mcpDescriptionCompressionEnabled true  ->  false
```

Verified persisted across a fresh MCP connection.

**Rationale for 131072 (128k):** comfortably above the ~90k average so ordinary work is untouched, well below the 1M window so a genuinely runaway context still gets relief. A first step, not a final answer.

**Rationale for disabling MCP description compression:** it saved 104 tokens in total while degrading the tool and skill descriptions that agents rely on to act correctly. The trade is indefensible at that ratio.

Unchanged and deliberately so: `enabled: true`, `strategy: standard`, `autoTriggerMode: lite`, `targetRatio: 0.7`, `preserveSystemPrompt: true`. Compression remains available as a pressure-relief valve.

## Preview works — and it revises the diagnosis

`omniroute compression preview` returns 401 when the key is passed via `--api-key`. It succeeds when passed as an **environment variable** using the admin key:

```bash
OMNIROUTE_API_KEY=$OMNIROUTE_ADMIN_API_KEY omniroute compression preview --file <request.json>
```

Result against `scratchpad/compression_probe.json` (real technical content — file paths, commit SHAs, ports, ruamel parameters, matcher strings):

```
263 tok -> 257 tok (2%)
techniques: ["filler_adverbs", "articles"]
validation: {"valid": true, "errors": [], "warnings": [], "fallbackApplied": false}
```

Every removal in the diff was an article or filler word (`"the "`, `"a "`, `"The "`, `"currently "`). **Every technical identifier survived verbatim** — `materialize_shared_agent_surface.py`, `convert_mcp_server_to_opencode`, `01bdeb8`, ports `7331`/`7332`, `write_file|patch`, `preserve_quotes=True, indent(mapping=2, sequence=4, offset=2), width=4096`, `-0.4000`, `10844 ms`. The engine also returns an explicit `preserved` list protecting version numbers and function calls.

**This weakens the earlier attribution.** An earlier revision of this document implied compression was a substantial cause of the 2026-07-26 context degradation. On this evidence it is far gentler than assumed: article-stripping with active identifier protection, not content mangling. The incident is better explained by the skill's executable-looking documentation example. Compression remains a plausible *contributing* factor, not a demonstrated cause.

## Scale test — compression is FLAT, and lossless for identifiers

Ran the preview across four payload sizes, from a 263-token probe to a 94k-token multi-turn conversation shaped like real work. Twenty canary identifiers (file paths, commit SHAs, ports, flag strings, error codes, memory IDs, version numbers, code-shaped tokens) were embedded and checked for exact survival.

| payload | original | compressed | saved | canaries surviving |
|---|---|---|---|---|
| 263 tok | 255 | 248 | 2.75% | 11/20 * |
| 7k | 7,133 | 6,920 | **2.99%** | **20/20** |
| 29k | 28,960 | 28,120 | **2.90%** | **20/20** |
| 94k | 94,039 | 91,325 | **2.89%** | **20/20** |

\* The nine "missing" canaries in the small probe were never in that input to begin with — verified against the source file. It is a measurement artifact, not stripping.

**Two findings, both decisive:**

1. **Compression does not scale with payload size.** It is flat at ~2.9% from 7k to 94k tokens. The scale-dependence hypothesis is dead — a 94k-token conversation loses the same ~3% of articles and filler as a 7k one.
2. **Identifier survival is perfect.** Every one of the 20 canaries survived verbatim at every size ≥7k, including `write_file|patch`, `E_GOVERNED_PROVENANCE_REQUIRED`, `mem_ms1dupqi_1bf00fc9d4a5`, `preserve_quotes=True`, `streamable_http`, and `0.9.28`.

### This exonerates compression

**Compression was not the cause of the 2026-07-26 context degradation.** A transform that removes ~3% articles while preserving every identifier cannot explain an agent losing an entire conversation's content and reaching for a documentation example instead. Earlier revisions of this document treated compression as a substantial and then a contributing factor; on this evidence it is neither. The cause was the skill's executable-looking example, plus whatever the agent's own context handling did — not this pipeline.

The `maxTokens` and MCP-description changes remain correct on their own merits (100% trigger rate at 9% context utilisation was pure overhead; 104 tokens saved was never worth degraded tool descriptions). They just should not be credited with fixing a problem they did not cause.

## Still to do

1. **Explain the 2.9% vs 13% reporting gap.** Live analytics report `lite` mode averaging **13%** across 228 requests, but every preview measured ~2.9%. Since scale is now ruled out, the difference is either a different engine path in production than the preview exercises, different content types (tool output and code dumps may compress far better than prose), or `avgSavingsPct` measuring something other than what preview reports. This is now a metrics-interpretation question, not a fidelity risk.
2. **Measure the new trigger rate.** Re-run `omniroute_compression_status` after a day of normal use and compare `compressedRequests` against `totalRequests`. If it still fires on most requests, raise to `262144`.
3. **Test the aggressive strategies before ever enabling one.** `aggressive`, `ultra`, and `omniglyph` are untested here. The safety demonstrated above is for `standard` only, and there is no reason to assume the harsher modes protect identifiers the same way. Reuse `scratchpad/compression_probe_xl.json` and the canary list.
4. **Consider `preserveSystemPrompt`'s blind spot.** It protects the system prompt only. If a strategy is ever needed at high volume, find out whether tool definitions and recent turns can be protected too.

## Note on the 99-tool surface

The OmniRoute MCP server exposes 99 tools. That is a large per-session context cost in every harness it is wired into. It ships `omniroute_tool_search` ("returns compact one-line TS signatures for token-efficient discovery") specifically for this. If the tool listing proves expensive, filter via a JanuScope lens rather than reaching for description compression again — compression trades correctness for bytes, filtering does not.
