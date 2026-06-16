---
name: reasoning-ensemble
description: >
  FLOSSI0ULLK Inline Reasoning Ensemble: use the Router for cheap mode
  classification (pass_through, single_strong, ensemble), and the Synthesizer
  for full ensemble deliberation on architectural decisions, multi-file
  refactors, ADR-class moves, or any substantive decision where being wrong has
  rollback cost. Also use when the user explicitly asks for debate, a second
  opinion, or multi-model/lens analysis.
license: AGPL-3.0
metadata:
  version: "0.1.1"
  date_landed: "2026-05-18"
  source: ".claude/skills/reasoning-ensemble/SKILL.md"
  related_research:
    - FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md
    - FLOSS/docs/research/2026-05-18-metaharness-unification.md
    - FLOSS/docs/research/2026-05-16-mdash-cfis-architectural-transfer.md
---

# Reasoning Ensemble Skill

Invoke selectively. This is not "debate every prompt"; it is debate for
substantive reasoning steps where blindspots matter.

## Router Only

When unsure whether a prompt deserves ensemble deliberation, ask the Router:

```bash
python C:/~shit/FLOSS/packages/reasoning_ensemble/router.py "<prompt>"
```

Expected JSON:

```json
{
  "mode": "pass_through | single_strong | ensemble",
  "reason": "<one-sentence justification>",
  "confidence": 0.0,
  "bias_applied": "tier4_similarity | force_flag | fallback_on_error | null",
  "duration_seconds": 0.0
}
```

If `bias_applied` is `tier4_similarity`, a past Tier-4 divergence on a
semantically adjacent prompt forced ensemble mode.

## Synthesizer

When the Router returns `ensemble`, the user tags `--debate`, or a substantive
decision needs a second lens:

```bash
python C:/~shit/FLOSS/packages/reasoning_ensemble/synthesizer.py "<prompt>"
```

The Synthesizer writes a durable draft under
`.agent-surface/reasoning/ensemble/` and appends a global `Action` to
`.agent-surface/activity.jsonl`.

Expected output includes:

- `tier`: `tier1`, `tier2`, or `tier4`
- `voter_responses`: per-voter raw responses and reasoning
- `clusters`: embedding-based response clusters
- `largest_cluster_fraction`: dominance signal
- `minority_coherent_voters`: dissent that passed the coherence guard
- `final_synthesis`: digest with consensus and named tensions

## When To Invoke

Always ensemble:

- Architectural proposals and ADR-class moves
- Multi-file refactors
- Decisions with blast radius beyond a single function
- Anything where a wrong answer has rollback cost
- Anything the user tags `--debate`

Default to `single_strong`:

- Single-file edits
- Code reads and explanations
- Routine synthesis
- Format conversions
- Memory recall

Use pass-through:

- File reads, directory listings, and grep results
- Status checks
- Acknowledgments

## Limits

- The v0.1 voter prompt still needs calibration; early voter responses included
  low-signal boilerplate.
- Tier-4 similarity bias only becomes useful after enough Tier-4 entries exist
  in `.agent-surface/reasoning/activity.jsonl`.
- Local models compete for GPU memory. On a 16GB system, calls may serialize.
- Synthesis drafts are not canon. Promotion still needs human/ADR/source-chain
  review.

## Current Voter Pool

Local Ollama voter pool: `phi4-mini`, `llama3.2-3b`, `granite-code-3b`, and
`qwen2.5-coder-3b`. The default Router is `phi4-mini:latest`; set
`FLOSS_ROUTER_MODEL=gemma3:12b-it-qat` if the stronger fallback is needed.

## References

- `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md`
- `FLOSS/docs/research/2026-05-18-metaharness-unification.md`
- `FLOSS/docs/research/2026-05-16-mdash-cfis-architectural-transfer.md`
- `FLOSS/docs/research/2026-05-15-working-todo-list.md`
- `FLOSS/packages/reasoning_ensemble/router.py`
- `FLOSS/packages/reasoning_ensemble/synthesizer.py`
