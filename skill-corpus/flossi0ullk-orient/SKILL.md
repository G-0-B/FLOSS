---
name: flossi0ullk-orient
description: Use when starting work in the FLOSSI0ULLK workspace, re-orienting after context loss, or deciding which canonical docs and corpora to load first before deeper research or code changes.
version: 0.2.0
---

# FLOSSI0ULLK Orientation

Regain orientation on **minimum tokens, maximum verifiability**. Read nothing before you know what is present and fresh.

## Token budget (hard)

| Tier | Target  | When                                                                    |
| ---- | ------- | ----------------------------------------------------------------------- |
| T0   | ≤ 500   | Probe only. Always.                                                     |
| T1   | ≤ 3 000 | Read `CONTEXT_L0.md` + canonical pointers.                              |
| T2   | ≤ 12 000| Escalate to `CONTEXT_L1.md`, `INDEX.md`, or a single routed corpus root.|
| T3   | open    | Only after T1+T2 proved insufficient for the *specific* task.           |

Stop at the lowest tier that answers the task. Do not pre-fetch.

## Core workflow

### Step 0 — Probe (always)

Run the probe to get a deterministic orientation packet. No mutation, no network.

```bash
python FLOSS/scripts/orient_probe.py --query "<task in one line>"
```

The packet reports: presence, mtime, size, and sha256 prefix for each canonical file; `.agent-surface/events/` queue depth; whether `context_router.py` is runnable; and a routed-corpus shortlist (if the router is present).

If the probe script itself is missing, fall back to the **Manual probe ladder** at the bottom of this file.

### Step 1 — Canon (T1)

In order, read only what the probe marked present and fresh:

1. `.agent-surface/context/CONTEXT_L0.md` — cheap re-orientation.
2. `INDEX.md` — authoritative map of the repo.
3. `FLOSS/CLAUDE.md` — agent-facing operating notes.
4. `FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` — **only** if the task touches governing principles.

### Step 2 — Route (T1 → T2)

```bash
python FLOSS/scripts/context_router.py "<query>" --format markdown --limit 4
```

Open **only the top-routed corpus roots**. If the router is absent or errors, fall back to `references/entry-points.md` in this skill.

### Step 3 — Escalate (T2)

If L0 + routed roots did not resolve the task, then — and only then:

- `.agent-surface/context/CONTEXT_L1.md`
- Relevant ADRs in `FLOSS/docs/adr/` for governance/architecture tasks.
- The specific subsystem corpus returned by the router.

### Step 4 — Intake/filewatch/consolidation tasks

For tasks touching intake, filewatch, consolidation, or cross-agent update flow, load (in order of increasing cost):

- `FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`
- `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`
- `FLOSS/scripts/watch_intake.py`
- `FLOSS/scripts/process_intake_events.py`

## Rules

- **No broad opens.** Never `ls -R`, never `cat` a directory-sized glob. If you find yourself wanting to, re-run the router.
- **`_reference/` is cold storage.** Treat it as a published research library, not live canon. Read only when the router returns it *and* the task requires it.
- **ADRs gate architecture/governance edits.** Do not propose changes to shared invariants without citing the relevant ADR (or explicitly opening a new one).
- **`.agent-surface/events/` is runtime queue state.** Not canon. Do not read event contents unless the task is the event-processing pipeline itself.
- **Prefer live artifacts over summaries.** Current code and source-chain records outrank docs; docs outrank `_reference/`.
- **Probe before read.** If you skipped Step 0 you are probably already over-reading.

## Failure ladder

| Missing artifact         | Fallback                                                              |
| ------------------------ | --------------------------------------------------------------------- |
| `orient_probe.py`        | Use Manual probe ladder below. Then open a P1 issue to restore probe. |
| `CONTEXT_L0.md`          | Read `INDEX.md` + `FLOSS/CLAUDE.md` only.                             |
| `INDEX.md`               | Use `references/entry-points.md` in this skill as the map.            |
| `context_router.py`      | Use `references/entry-points.md`; flag the regression.                |
| `.agent-surface/` absent | Treat as cold-start. Do not infer runtime state.                      |

## Manual probe ladder (probe-script-absent fallback)

```bash
for f in \
  .agent-surface/context/CONTEXT_L0.md \
  .agent-surface/context/CONTEXT_L1.md \
  INDEX.md \
  FLOSS/CLAUDE.md \
  FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md \
  FLOSS/scripts/context_router.py \
  FLOSS/scripts/orient_probe.py; do
  if [ -f "$f" ]; then
    printf '%s\t%s\t%s\n' "present" "$(stat -c '%y %s' "$f" 2>/dev/null || stat -f '%Sm %z' "$f")" "$f"
  else
    printf 'MISSING\t-\t%s\n' "$f"
  fi
done
ls -1 .agent-surface/events/ 2>/dev/null | wc -l  # runtime queue depth
```

## Self-audit at end of task

Before closing the task, answer:

1. Which tier did I stop at? (T0/T1/T2/T3)
2. What canonical artifacts did I *actually* read — and why each?
3. Did I open anything under `_reference/` or a broad directory? If yes, justify.
4. Did any ADR govern my change? Cite it.
5. Did I mutate `.agent-surface/events/` or source-chain state? If yes, intentionally?

## References

- `references/entry-points.md` — canonical file map with tier tags and one-line purpose.

## Changelog

- **0.2.0** — Added Step 0 probe, token-budget tiers, failure ladder, manual fallback, self-audit. Tightened rules. Shipped missing `references/entry-points.md` and `scripts/orient_probe.py`.
- **0.1.0** — Initial checklist.
