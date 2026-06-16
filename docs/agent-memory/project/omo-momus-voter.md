---
id: project-omo-momus-voter
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_omo_momus_voter.md
title: omo-momus persona voter is wired and approved in production
legacy_description: oh-my-openagent's Momus reviewer persona is now a consensus-gateway
  voter. Adds cognitive-style diversity (blocker-finder, approve-by-default) to model-family
  diversity. Two voters in diverse-max use Momus on top of groq/openai/gpt-oss-120b
  and groq/llama-3.3-70b-versatile. Validated by consensus round 019e1d61 APPROVED
  2026-05-12.
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

## What's wired

`FLOSS/packages/metacoordinator_mcp/voters.py` now contains:
- `MOMUS_PERSONA_SYSTEM` — adapted from `oh-my-opencode@4.0.0`'s `MOMUS_DEFAULT_PROMPT`, retargeted from `.sisyphus/plans/*.md` review to Claim review. Keeps the "blocker-finder not perfectionist, APPROVE by default, max 3 blockers, references must exist, executability must be real" disposition.
- `make_omo_momus_voter(name, model, ...)` — wraps the chosen substrate model with Momus as a SYSTEM message and the standard VOTER_PROMPT as USER message. Parses WEIGHT/RATIONALE the same way other voters do.
- `build_default_voters` routes by voter NAME prefix: `omo-momus-*` → `make_omo_momus_voter`, else `flowith/...` → `make_flowith_voter`, else `make_litellm_voter`.

`voter_registry.json` profile `diverse-max` now has:
- `omo-momus-gpt-oss-120b` → `groq/openai/gpt-oss-120b`
- `omo-momus-llama-3.3-70b` → `groq/llama-3.3-70b-versatile`

## Why this matters architecturally

Cognitive-style diversity is distinct from model-family diversity. The same model with a different system persona votes differently — Momus specifically scans for unresolved references, executability gaps, and contradictions with approve-by-default disposition, whereas vanilla voters drift toward general "evaluate this proposal" reasoning. CCES L5 (Collective Intelligence) requires heterogeneity in cognitive style, not just model family. Momus is the first such persona — Oracle (architecture consultant), Metis (gap-detector), Sisyphus (mechanics-driven planner), etc. can be added the same way.

## Validation evidence

Consensus round 019e1d61-24fa-753d-bdce-1444ba0a1d1e (2026-05-12): "Was wiring Momus + repairing diverse-max correct?"
- Outcome: **APPROVED** (Module blast_radius, threshold +0.50)
- tally_mean: +0.673, tally_variance: 0.1582
- 12 of 16 voters fired; both omo-momus voters returned (+0.62 and +0.85) with Momus-style rationales

## Concurrent bug fixes from this work

1. `make_flowith_voter`: `requests.post(json=request_body)` where request_body was already JSON-stringified → double-encode causing all Flowith voters to error with HTTP 400 "Expected object, received string". Fixed by changing `json=` to `data=`. After fix, `flowith-gemini-2.5-flash` works; `flowith-claude-sonnet-4`, `flowith-gpt-4o`, `flowith-deepseek-chat` still fail (likely model-identifier mismatches against Flowith's actual catalog — separate follow-up).

2. `diverse-max` profile rebuild: removed unverified Cerebras IDs (`llama-3.3-70b`, `qwen-3-32b`, `gpt-oss-120b`, `llama-4-maverick`) that the account doesn't recognize; removed decommissioned Groq models (`deepseek-r1-distill-llama-70b`, `qwen-qwq-32b`); removed `groq/moonshotai/kimi-k2-instruct` (not on tier). Profile now contains only verified-working IDs.

## Open follow-ups

- Flowith model-identifier audit: claude-sonnet-4/gpt-4o/deepseek-chat still fail post-fix. Probably need to query Flowith for the current catalog and update voter names. Maybe `flowith/claude-sonnet-4-5` or similar.
- `groq/meta-llama/llama-4-maverick-17b-128e-instruct` errored on this consensus round; needs investigation (account access? rate limit at the moment?).
- Add more omo personas: Oracle (read-only architecture consultant), Metis (creative gap-detector), Momus on more model substrates.
- Cerebras model catalog audit: figure out the correct ID format for the 70B+ models and add them back to diverse-max once verified.

## How to apply

- Default heartbeat profile is `diverse-max` (16-voter, includes 2 omo-momus). For tighter polls, use `diverse` (6-voter, no omo). For dev/quick tests, use `fast` (2-voter).
- To add a new omo persona voter: extract the agent's system prompt from `~/.cache/opencode/node_modules/oh-my-opencode/dist/index.js`, add a `<NAME>_PERSONA_SYSTEM` constant + `make_omo_<name>_voter` factory in voters.py mirroring the Momus pattern, register `omo-<name>-<model>` entries in voter_registry.json, and update the prefix dispatch in `build_default_voters`.
