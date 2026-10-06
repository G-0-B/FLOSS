# Model-identity anomaly — 2026-08-29

Eleven reviewer outputs for the
[provenance-anchor Lane A packet](../2026-08-26-provenance-anchor/PACKET.md),
collected by the operator across different harnesses, models and tool
configurations. Saved because several models self-reported an identity that did
not match what was selected.

| | |
|---|---|
| Raw artifacts | `*.json` at this level — byte-preserved, `-text` in `.gitattributes`, committed before any analysis |
| Derived | `normalized/` — see *Derivation* below. Never cite these as evidence |
| Operator ground truth | **the filenames**, which encode harness, selected model and tool configuration |

## What the corpus actually says

### 1. Nobody said "Sonnet 4.6"

The recollection that prompted saving these was approximate. The record is:

| Self-reported | Claimed by |
|---|---|
| `claude-sonnet-4-5` | `perplexity-gemini-3-7-thinking-all-tools`, `perplexity-grok-4-6-thinking-all-tools-github-mcp` |
| `claude-3.5-sonnet-20241022` | `unsure-sonnet-3-5-no-tools` |
| `Antigravity` | `antigravity-gemini-3-1-pro-no-tools` — **the harness name reported as the model** |
| `Perplexity` | `perplexity-gpt-5-6-terra-...` — the harness name again |
| `OpenAI API model (exact identity not disclosed…)` | `pioneer-gpt-5-6-sol-api-no-tools` — **the only reviewer that declined to claim** |

That correction is the point of saving artifacts rather than trusting memory,
and it lands in the operator's favour: the anomaly is real, and it is a different
anomaly than remembered.

### 2. The identity collision did NOT indicate a shared reviewer

Two of three Perplexity runs — different selected models — both reported
`claude-sonnet-4-5`, both reported the identical harness string
`Perplexity MCP + github_mcp_direct + execute_code`, and both reported the
identical `tools_used`. That is a strong-looking signal.

**Their findings are disjoint.** Pairwise φ between them is **−0.159**; across
the whole Perplexity trio every pair is negative. Whatever is shared, it is not
producing shared output. On the measurement that matters they behaved as
different reviewers.

### 3. The actual duplicate is somewhere else entirely

`deepseek-web-no-tools.json` and `unsure-sonnet-3-5-no-tools.json` are
**identical documents** — all six findings, every evidence string, the
`refutations`, `predicted_majority` and `where_you_expect_to_be_alone` — except
for one field:

```
deepseek-web-no-tools      reviewer.model = "deepseek-chat"
unsure-sonnet-3-5-no-tools reviewer.model = "claude-3.5-sonnet-20241022"
```

φ = **1.000**, the only positive pair in the entire matrix.

Free-form multi-thousand-character output does not coincide. Either both files
are one generation, or one surface served both requests and emitted a different
identity string on each call. **Two candidates the operator can resolve and I
cannot:** whether these were separate submissions at all, and whether decoding
was deterministic.

For the measurement the cause does not matter: **they are one reviewer and must
be counted once.**

### 4. Harness-string collisions happen by confabulation

That same pair also reported the identical harness string —
`read-only reasoning against provided artifact summary` — which reads like
evidence of shared infrastructure and is nothing of the kind: the packet asks for
`harness`, and a model with no real answer describes its situation. Two
independent reviewers can invent the same phrase.

So **a matching harness string is not evidence of a matching harness.** What
distinguishes the Perplexity case is that its collision includes specific
internal tool names — `github_mcp_direct`, `execute_code` — which are not phrases
two models would independently invent. Specific tokens colliding is a different
claim from generic descriptions colliding, and only the former is evidence.

### 5. Structured output is not reliably structured

**2 of 11 (18%) failed to parse as JSON**, from two unrelated causes:

- `perplexity-gpt-5-6-terra-…` — the harness appended markdown citations
  (`[github](https://…)`) **into the JSON**, after closing string quotes,
  despite the explicit "return ONLY the JSON schema" instruction. Harness
  contamination, not a model failure.
- `pioneer-gpt-5-6-sol-…` — unescaped `"` inside string values where the model
  quoted the artifact verbatim. Generation failure.

The protocol leans on that schema for comparability and for automation. An 18%
hard-failure rate is a finding about the protocol, not about these two files.

### 6. Tool access and finding volume — suggestive, not measured

Reviewers with retrieval raised more: grok+GitHub MCP 11, perplexity-gemini 9,
meta 8, perplexity-grok 8, glm 7. Untooled: deepseek/unsure 6 (one reviewer),
antigravity 4. Directionally consistent with the tool-access hypothesis, but
**finding count is not finding quality**, n is small, and none of it is
adjudicated. It is not evidence yet.

## What could NOT be measured

`review_independence.py` **refuses to report n_eff on this corpus**, correctly.
Mean pairwise φ is −0.096; only **6 of 62 findings (10%)** were raised by more
than one reviewer. Text matching on `location::claim` does not recognise the same
defect worded differently, and near-disjoint sets are anti-correlated by
construction — so the negative mean measures the matcher, not the panel.

Before the fix the tool reported `n_eff = 71.33` for a 10-reviewer panel and an
"independence ratio" of 713%. A measurement at the wrong grain returned a
confident wrong answer instead of "unknown" — in the instrument built to detect
exactly that.

**A human merge pass over the 62 findings, then `--merge`, is what turns this
corpus into a real n_eff.** That is the outstanding work, and it is the operator's
call because merging findings is a judgment about what counts as the same defect.

## Derivation

`normalized/` is derived, not evidence. `MANIFEST.json` records per-file status.

- `model_selected` = the verbatim filename (operator ground truth).
- `model_self_reported` = whatever the model claimed. `self_reported_harness`
  likewise.
- `harness` = the leading filename token. **This is my inference from the naming,
  not an operator statement**, and should be corrected where wrong.
- One repair: `perplexity-gpt-5-6-terra-…` had 3 injected `[github](url)`
  citations removed from outside the JSON strings, array separators preserved,
  no character inside any string value altered.
- One refusal: `pioneer-gpt-5-6-sol-…` is left broken and excluded. Repairing it
  requires rewriting quotes *inside* string values, which alters evidence
  content. **Remove contamination; never rewrite content.**

## Consequences for the protocol

1. **Count reviewers by measured overlap, not by label.** Two files with φ = 1.000
   are one reviewer whatever their filenames say.
2. **An identity collision is not a routing finding.** Perplexity's collided and
   its reviewers still behaved independently.
3. **Require the merge pass before quoting any n_eff.** The tool now refuses
   rather than inventing one, but the refusal is not a substitute for doing it.
4. **Budget for an ~18% parse-failure rate**, and separate harness contamination
   from generation failure when it happens — they have different fixes.
