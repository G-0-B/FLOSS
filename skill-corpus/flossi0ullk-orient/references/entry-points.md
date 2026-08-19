# Entry Points (FLOSSI0ULLK canonical map)

Purpose: the minimal, probe-first map of canonical entry points. Tiered by token cost so an agent can stop at the cheapest layer that answers the task.

> **Reconciled 2026-06-11** against the live repo (branch `codex/document-holochain-zomes`): every former verification tag is resolved below as CONFIRMED or corrected-in-place. Re-verify after major tree restructures.

## T0 — Probe layer

Read nothing. Run:

```bash
python FLOSS/scripts/orient_probe.py --query "<task>"
```

If missing, use the Manual probe ladder in `SKILL.md`.

## T1 — Cheap canon (≤ 3 000 tokens total)

| File                                                                    | Purpose                                                  | Read when                                     |
| ----------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------- |
| `.agent-surface/context/CONTEXT_L0.md`                                  | Distilled re-orientation context; hand-curated           | Every cold start where present                |
| `INDEX.md`                                                              | Repo-root map                                            | When `L0` is absent or lists you to `INDEX`   |
| `FLOSS/CLAUDE.md`                                                       | Agent operating notes for this workspace                 | Every cold start                              |
| `FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md`                  | Governing principles kernel                              | Only when task touches P1–P5 or invariants    |

## T1.5 — Routing

| File                                                                    | Purpose                                                  | Read when                                     |
| ----------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------- |
| `FLOSS/scripts/context_router.py`                                       | Query → ranked corpus roots                              | Before opening any corpus tree                |

Expected call contract:

```bash
python FLOSS/scripts/context_router.py "<query>" --format markdown --limit 4
```

Expected output: markdown list of ranked corpus roots, each with a one-line justification.

Contract CONFIRMED live 2026-06-11: `query` is positional (`nargs="*"`), `--format {json,markdown}`, `--limit` defaults to **3** — pass it explicitly; optional `--manifest`.

Routing manifests and bootstrap (companions to the router):

- `FLOSS/shared-context-surface.json`
- `FLOSS/shared-skill-surface.json`
- `.agent-surface/context/CONTEXT_BOOTSTRAP.md`

Typical queries:

```bash
python FLOSS/scripts/context_router.py "consensus claim vote provenance" --format markdown --limit 4
python FLOSS/scripts/context_router.py "radicle holochain architecture" --format markdown --limit 4
python FLOSS/scripts/context_router.py "shared skills mcp hooks" --format markdown --limit 4
```

## T2 — Escalation layer (≤ 12 000 tokens)

| File / Root                                                             | Purpose                                                                        |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `.agent-surface/context/CONTEXT_L1.md`                                  | Deeper hand-curated context when L0 is insufficient                            |
| `FLOSS/docs/adr/`                                                       | Architecture Decision Records — read before any governance/architecture edit   |
| `FLOSS/docs/adr/INDEX.md`                                               | ADR index — start here before opening individual ADRs                          |
| *Router-returned corpus roots*                                          | Subsystem-specific docs and code trees                                         |

### Task-specific T2 entry points

**Intake / filewatch / consolidation / cross-agent update** — load in order:

1. `FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`
2. `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`
3. `FLOSS/scripts/watch_intake.py`
4. `FLOSS/scripts/process_intake_events.py`

**Shared agent surface / MCP servers / materializers / context manifests** — route through the `flossi0ullk-shared-surface` skill.

**Consensus gateway / voter rosters / post-write hooks / source-chain claims and votes** — route through the `flossi0ullk-consensus-gateway` skill.

## T3 — Open exploration (only after T1+T2 proved insufficient)

| Root                                                                    | Rules                                                                               |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `FLOSS/ARF/dnas/<dna>/zomes/`                                             | Rust/Holochain zomes (integrity + coordinator). CONFIRMED — no `FLOSS/crates/` exists. |
| `FLOSS/ARF/dnas/`                                                         | DNA roots: `rose_forest` (active workspace), `infinity_bridge` (pre-migration, excluded). CONFIRMED. |
| `FLOSS/docs/`                                                            | General docs tree. Prefer ADR subfolder.                                            |
| `FLOSS/scripts/`                                                         | Utility scripts. Known: `context_router.py`, `orient_probe.py`, `watch_intake.py`,  |
|                                                                         | `process_intake_events.py`                                                          |
| `_reference/`                                                            | **Cold storage only.** Published research library. Do not use as live canon.        |

## Runtime state (never canon)

| Path                              | What it is                                                  |
| --------------------------------- | ----------------------------------------------------------- |
| `.agent-surface/events/`          | Runtime queue. Check depth (count of files), not contents,  |
|                                   | unless the task is the event pipeline itself.               |
| `.agent-surface/events/locks/*.lock` | CONFIRMED writer convention (`lock_file()` in `watch_intake.py` / `process_intake_events.py`). If present, intake write in progress — wait. Probe also scans `.agent-surface/context/` defensively. |

## Cross-skill links

- `flossi0ullk-shared-surface` — shared agent surface, MCP servers, manifests.
- `flossi0ullk-consensus-gateway` — local consensus gateway, voter/provider rosters.

## Staleness policy

Use the probe's mtime fields:

- L0 older than 14 days → flag as potentially stale; check `INDEX.md` anyway.
- ADR older than relevant code edit → re-read the ADR; your model of canonical decisions may be wrong.
- `_reference/` entries have no freshness guarantee — they are a library, not a canon.
