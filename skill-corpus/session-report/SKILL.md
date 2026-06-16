---
name: session-report
description: Generate an explorable HTML report of Claude Code session usage (tokens, cache, subagents, skills, expensive prompts) from ~/.claude/projects transcripts. Use at end-of-session, end-of-week, or when investigating token spend / cache-hit anomalies / which subagent or skill is eating budget.
---

# Session Report — Claude Code Usage Retrospective

Produce a self-contained HTML report of Claude Code usage and save it to the current working directory.

## Source bundle

The bundled analyzer + template live under the marketplace plugin at:
`C:\Users\kalis\.claude\plugins\marketplaces\claude-plugins-official\plugins\session-report\skills\session-report\`

- `analyze-sessions.mjs` — extracts data from `~/.claude/projects/*` transcripts
- `template.html` — interactive report shell

These are NOT copied into FLOSS/skill-corpus to avoid drift from upstream. This skill points at them directly.

## Steps

1. **Get data.** Run the bundled analyzer (default window: last 7 days; honor a different range if the user passed one — `24h`, `30d`, or `all`):
   ```sh
   node "C:\Users\kalis\.claude\plugins\marketplaces\claude-plugins-official\plugins\session-report\skills\session-report\analyze-sessions.mjs" --json --since 7d > /tmp/session-report.json
   ```
   For all-time, omit `--since`. On Windows substitute a writable temp dir (e.g. `$env:TEMP\session-report.json`).

2. **Read** `/tmp/session-report.json`. Skim `overall`, `by_project`, `by_subagent_type`, `by_skill`, `cache_breaks`, `top_prompts`.

3. **Copy the template** to a timestamped HTML in the current working directory:
   ```sh
   cp "C:\Users\kalis\.claude\plugins\marketplaces\claude-plugins-official\plugins\session-report\skills\session-report\template.html" "./session-report-$(date +%Y%m%d-%H%M).html"
   ```

4. **Edit the output file** (use Edit, not Write — preserve the template's JS/CSS):
   - Replace contents of `<script id="report-data" type="application/json">` with the full JSON from step 1.
   - Fill `<!-- AGENT: anomalies -->` with **3–5 one-line findings**. Express figures as **% of total tokens** wherever possible (total = `overall.input_tokens.total + overall.output_tokens`). One line per finding, exact markup:
     ```html
     <div class="take bad"><div class="fig">41.2%</div><div class="txt"><b>cc-monitor</b> consumed 41% of the week across just 3 sessions</div></div>
     ```
     Classes: `.take bad` red, `.take good` green, `.take info` blue. The `.fig` is one short number (`%`, count, or multiplier like `12×`). The `.txt` is one plain-English sentence naming the project/skill/prompt; wrap the subject in `<b>`.
     Look for: a project or skill eating a disproportionate share, cache-hit <85%, a single prompt >2% of total, subagent types averaging >1M tokens/call, cache breaks clustering.
   - Fill the `<!-- AGENT: optimizations -->` block (bottom of page) with 1–4 `<div class="callout">` suggestions tied to specific rows.
   - Do not restructure existing sections.

5. **Report** the saved file path. Do not open it.

## FLOSSI0ULLK-specific anomaly checks

When generating the narrative, also flag:

- Heartbeat-loop spend > 30% of weekly total → potential STOP-gate drift; see `FLOSS/docs/specs/heartbeat-runtime-budget.spec.md`.
- A single voter/model > 50% of consensus-gateway spend → diversity policy violation; check `packages/metacoordinator_mcp/voter_registry.json`.
- Synthesis drafts staged > generated → backpressure should kick in; check `FLOSS_SYNTHESIS_STAGING_CAP`.
- A single skill from `skill-corpus/` >15% of total → consider whether the skill is too heavy-context or duplicated across harnesses.

## Notes

- The template is the source of interactivity. Your job is data + narrative, not markup.
- Keep commentary terse and specific — reference actual project names, numbers, timestamps from the JSON.
- `top_prompts` already includes subagent tokens and rolls task-notification continuations into the originating prompt.
- If JSON > 2MB, trim `top_prompts` and `cache_breaks` to 100 entries before embedding.
- Cross-harness note: this skill targets the **Claude Code** transcript layout under `~/.claude/projects/`. Codex/Gemini/OpenCode transcripts live elsewhere and need their own session-report variants — track as a future skill if the user runs into the same anomaly-finding need on those harnesses.

## Provenance

Original skill: `claude-plugins-official/session-report`. Adapted for FLOSSI0ULLK: added the heartbeat/voter/synthesis/skill anomaly checks tied to the FLOSSI0ULLK runtime surfaces, noted cross-harness boundary.
