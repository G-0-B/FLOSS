# Context Continuation: orient-skill v0.2.0 handoff

```yaml
# --- UpgradableArtifact Header ---
id: "ccp-orient-skill-v020-handoff"
version: "1.0.0"
kind: "context_continuation_packet"
status: "Accepted"
updated: "2026-06-09"
supersedes: []
truth_status: "Specified"  # payloads Verified in synthetic harness; Unverified against live repo
evidence_sources:
  - "claude.ai web session 2026-06-09 (this packet's origin)"
  - "flossi0ullk-orient SKILL.md v0.1.0 (read in-session from /mnt/skills/user/)"
  - "Synthetic smoke tests: happy / lock / cold-start / json paths, all passing"
upgrade_path: "Receiving instance reconciles [VERIFY] items against live repo -> bumps payload truth_status -> installs"
rollback_plan: "Do not install payloads; v0.1.0 skill remains untouched until Step 6 below"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
friction_tier: "low"  # this doc; embedded payloads are medium (skill + script)
```

```yaml
# --- Provenance Packet (Kernel v1.3.1 §8) ---
timestamp: "2026-06-09T00:00:00Z"  # origin session date; exact time not material
author_agent: "Claude (Anthropic, claude.ai web session — NO repo access)"
human_collision_node: "Anthony (kalisam)"
source_systems: ["claude.ai web", "flossi0ullk-orient skill v0.1.0", "userMemories", "project knowledge (not consulted for payloads)"]
claim_type: ["proposal", "repo_assumption"]  # repo assumptions are flagged [VERIFY] throughout
payload:
  summary: |
    Anthony added flossi0ullk-orient v0.1.0. Origin Claude critiqued it:
    (1) references/entry-points.md promised but absent; (2) checklist not
    protocol — no probe step, no token budget, no failure ladder; (3) single
    point of failure on context_router.py with undocumented contract.
    Built v0.2.0: upgraded SKILL.md (probe-first, T0-T3 token tiers, failure
    ladder, self-audit), orient_probe.py (stdlib-only, no-mutation, exit 2 on
    locks), entry-points.md (the missing map, [VERIFY]-tagged), CHANGELOG.
    Probe smoke-tested on 4 synthetic paths. NOT validated against live repo
    — origin sandbox had no FLOSS checkout. All four files embedded below
    with sha256. Receiving instance must verify repo reality BEFORE install.
  evidence: ["sha256 digests per payload", "smoke-test transcript in origin session", "SKILL.md v0.1.0 text (quoted assumptions)"]
  risks: ["paths inferred not observed", "router signature assumed", "lock convention assumed", "install-before-verify would propagate fiction into canon"]
  benefits: ["deterministic T0 probe before any canon read", "token spend known in advance", "missing-file failure ladder", "integrity-verifiable handoff (this packet)"]
next_action: "Run Bootstrap Protocol Step 0-3 against the live repo; reconcile [VERIFY] table; only then install."
```

---

## 0. READ ME FIRST (receiving instance)

You are a Claude instance with **local filesystem access** to Anthony's machine and the FLOSS repo. The origin instance (claude.ai web) had **no** repo access — every claim below about repo layout is an inference, tagged `[VERIFY]`. Your first job is reconciliation, not installation.

**Source authority (binding):** repo branch state > CURRENT_STATE file > repo docs > project-knowledge uploads > conversation history > memory > **this packet**. This packet is conversation-derived: when it conflicts with the repo, **the repo wins and you say so** — fail closed, don't blend.

**Operating contract:** Anthony's kernel v1.3.1 applies (Intent Echo → lenses → ternary decision with pre-decision spectrum → actions → 5-box check). Anti-sycophancy is load-bearing. He answers piecemeal across turns — re-ask open questions rather than dropping them.

**What this packet is NOT:** a project snapshot. It deliberately does not duplicate project canon (CONTEXT_L0/L1, INDEX.md, ADRs) — those live in the repo and outrank this. This packet carries exactly one thread: the orient-skill v0.2.0 work.

---

## 1. Thread context (one paragraph)

The `flossi0ullk-orient` skill exists to let agents regain orientation in the FLOSSI0ULLK workspace on minimum tokens. v0.1.0 was a 40-line checklist that (a) referenced a `references/entry-points.md` it didn't ship, (b) gave agents no way to verify which canonical files exist before attempting reads — forcing attempt-then-recover, the exact token spray the skill exists to prevent, and (c) leaned on `FLOSS/scripts/context_router.py` with no documented contract or fallback. v0.2.0 (payloads below) fixes all three: a mandatory deterministic probe (Step 0), explicit token-budget tiers, a per-artifact failure ladder, and the missing reference map.

## 2. Session decision log (ternary + truth status)

| # | Decision | State | Truth status | Notes |
|---|----------|-------|--------------|-------|
| 1 | Probe-first redesign of orient skill (Step 0 mandatory) | +1 shipped | Verified (synthetic) / Unverified (live repo) | 4 smoke paths pass: happy, lock→exit 2, cold-start, JSON |
| 2 | Token tiers T0≤500 / T1≤3k / T2≤12k / T3 open | +1 shipped | Specified | Thresholds are first-guess targets; tune after live use |
| 3 | Failure ladder + manual shell fallback in SKILL.md | +1 shipped | Specified | |
| 4 | Ship `references/entry-points.md` with `[VERIFY]` tags | +1 shipped | Specified | Tags mark inferred-not-observed paths |
| 5 | Shell-only probe instead of Python | −1 rejected | — | Less testable, harder to extend |
| 6 | `watch` semantics inside probe | −1 rejected | — | Crosses scope boundary into context-daemon territory |
| 7 | Probe auto-reads CONTEXT_L0.md contents | −1 rejected | — | Violates no-mutation/no-assumption-about-size contract |
| 8 | Metaprompt-Kernel vs ADR/Spine read-precedence in skill | 0 hold | Unverified | Kept v0.1.0 ordering; flagged as possible inversion needing ADR — do not silently change |
| 9 | pytest suite formalizing the 4 smoke scenarios | 0 hold | Aspirational | Offered; Anthony has not answered (re-ask) |
| 10 | CI / pre-commit canary running `orient_probe.py --json` | 0 hold | Aspirational | Offered; Anthony has not answered (re-ask) |

## 3. Deliverable state

Four files, embedded verbatim in §7 with sha256 digests. Origin also staged them as downloadable outputs in the web chat (`flossi0ullk-orient-v0.2.0/`), but **treat §7 as canonical for this handoff** — rematerialize from here and verify hashes; do not depend on the chat download.

| File | Target location after install | sha256 |
|------|-------------------------------|--------|
| `SKILL.md` | skill folder (replaces v0.1.0 `SKILL.md`) | `177dcd1b375eea57cec2b177083243ee7abad4c17a7d04eed56ccc9f9c2619a4` |
| `references/entry-points.md` | skill folder `references/` | `fc5b1d24e05ed450d314918df582ce36a3e2bd83e1d4607225602aff1ac6061a` |
| `CHANGELOG.md` | skill folder | `37c3f0a2900c472c136bae1f70d310999c647d85f0444d3967400c403afdd54a` |
| `scripts/orient_probe.py` | **repo**: `FLOSS/scripts/orient_probe.py` (NOT the skill folder — SKILL.md calls it at that repo path) | `e603f993c1a21166ecf669674f82fa1a29798dd662c0cb33042f96c8fc821097` |

Skill-folder location `[VERIFY]`: wherever `flossi0ullk-orient` v0.1.0 currently lives on Anthony's machine. Candidates: `~/.claude/skills/flossi0ullk-orient/`, a project-local `.claude/skills/`, or a Cowork capabilities directory. **Ask Anthony or locate v0.1.0 by its content before writing anything.**

## 4. Bootstrap Protocol (fail-closed; run in order)

```
STEP 0 — Locate. Find repo root (expect FLOSS/ subdir and repo-root
         .agent-surface/, INDEX.md). Find the live v0.1.0 skill folder.
         If either is not where expected: STOP, ask Anthony. Do not guess.

STEP 1 — Baseline. git status, current branch, last ~5 commits, and read
         CURRENT_STATE file if present. This is your source-authority anchor.

STEP 2 — Probe reality BEFORE installing. Run the Manual Probe Ladder
         (§7 SKILL.md payload, bottom section) against the live repo.
         You now have ground truth for every [VERIFY] tag.

STEP 3 — Reconcile. For each [VERIFY] item in entry-points.md (§7 payload),
         mark CONFIRMED / REFUTED / ABSENT. Edit the payload copy accordingly
         BEFORE install. Report the reconciliation table to Anthony.

STEP 4 — Router contract. Read FLOSS/scripts/context_router.py's argparse
         block. If signature differs from assumed
         (`context_router.py "<q>" --format markdown --limit N`),
         patch try_router() in orient_probe.py payload before install.

STEP 5 — Lock convention. Confirm `.agent-surface/context/*.lock` is the real
         in-progress marker (grep the consolidation/intake scripts). If it's
         `.tmp` or other, patch LOCK_GLOB / lock_files() before install.

STEP 6 — Install (only now). Write the four files to targets in §3, verify
         sha256 of unmodified files (SKILL.md/CHANGELOG should match exactly;
         entry-points.md and orient_probe.py may legitimately differ after
         Steps 3-5 — record new hashes + a one-line diff note).

STEP 7 — Live validation. From repo root:
           python FLOSS/scripts/orient_probe.py --query "post-install validation"
         Present the packet to Anthony. Bump decision #1 truth_status to
         Verified (live) in your session notes if clean.

STEP 8 — Open the LATER items with Anthony (§6) — do not auto-build them.
```

## 5. Open questions (re-ask; do not drop)

**Self-answerable from repo (answer them yourself in Steps 4–5, then report):**
1. Real `context_router.py` CLI signature?
2. Real lock/in-progress file convention under `.agent-surface/`?
3. Does `.agent-surface/context/CONTEXT_L0.md` actually exist on the current branch, and how stale is it?

**Need Anthony (ask early, accept piecemeal answers):**
4. pytest suite formalizing the probe's 4 smoke scenarios — wanted? (decision #9)
5. CI / pre-commit canary on probe `--json` output — wanted, and which CI runs it? (decision #10)
6. Metaprompt-Kernel vs ADR/Spine read-precedence in the skill: open an ADR, or confirm current ordering is intentional? (decision #8 — origin flagged a *suspected* inversion; this is Unverified, not asserted)
7. Should `flossi0ullk-shared-surface` and `flossi0ullk-consensus-gateway` delegate their Step 0 to this skill instead of duplicating canon lists? (canon-drift prevention)

## 6. Next actions

**NOW (this session, in order):** Bootstrap Steps 0–7 above. That's the whole NOW list — resist adding to it.

**LATER (gated on Anthony's answers in §5):**
- pytest suite for probe (#4)
- CI/pre-commit canary (#5)
- Cross-skill Step-0 delegation edits (#7)
- Tune token-tier thresholds after ~a week of live probe use
- Probe output as post-write artifact in the Context Continuation pipeline `[VERIFY: pipeline name/shape — origin referenced "Context Continuation Artifact v0.2.0" from prior context it could not confirm]`

**NEVER (rejected this thread; do not regenerate):**
- Shell-only rewrite of the probe (decision #5)
- Watch/daemon semantics inside the probe (decision #6)
- Probe reading canon file *contents* (decision #7)
- Installing payloads before Steps 0–5 verification
- Treating this packet as authoritative over the repo

## 7. Payloads (canonical for this handoff)

Each payload sits between `BEGIN_FILE` / `END_FILE` sentinel lines inside a 4-backtick fence. Write the bytes between sentinels **verbatim** (no added trailing newline beyond what's present), then `sha256sum` against §3. Payloads appended below by the origin instance directly from the staged files — not retyped.

<!-- PAYLOADS_APPENDED_BELOW -->

### Payload: `SKILL.md` → target: `<skill-folder>/SKILL.md`

````
BEGIN_FILE SKILL.md
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
END_FILE SKILL.md
````

### Payload: `references/entry-points.md` → target: `<skill-folder>/references/entry-points.md`

````
BEGIN_FILE references/entry-points.md
# Entry Points (FLOSSI0ULLK canonical map)

Purpose: the minimal, probe-first map of canonical entry points. Tiered by token cost so an agent can stop at the cheapest layer that answers the task.

> **[VERIFY]** tags mark entries whose exact path or existence should be confirmed by the probe on your working branch. They are derived from the orient SKILL.md declarations and known workspace conventions as of v0.2.0 of this skill.

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

## T2 — Escalation layer (≤ 12 000 tokens)

| File / Root                                                             | Purpose                                                                        |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `.agent-surface/context/CONTEXT_L1.md`                                  | Deeper hand-curated context when L0 is insufficient                            |
| `FLOSS/docs/adr/`                                                       | Architecture Decision Records — read before any governance/architecture edit   |
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
| `FLOSS/crates/`                                                          | Rust/Holochain code. Open a single crate after router. **[VERIFY]** root name       |
| `FLOSS/dna/` or `FLOSS/zomes/`                                           | Holochain DNA definitions. **[VERIFY]** layout                                      |
| `FLOSS/docs/`                                                            | General docs tree. Prefer ADR subfolder.                                            |
| `FLOSS/scripts/`                                                         | Utility scripts. Known: `context_router.py`, `orient_probe.py`, `watch_intake.py`,  |
|                                                                         | `process_intake_events.py`                                                          |
| `_reference/`                                                            | **Cold storage only.** Published research library. Do not use as live canon.        |

## Runtime state (never canon)

| Path                              | What it is                                                  |
| --------------------------------- | ----------------------------------------------------------- |
| `.agent-surface/events/`          | Runtime queue. Check depth (count of files), not contents,  |
|                                   | unless the task is the event pipeline itself.               |
| `.agent-surface/context/*.lock`   | **[VERIFY]** If present, router/write in progress — wait.   |

## Cross-skill links

- `flossi0ullk-shared-surface` — shared agent surface, MCP servers, manifests.
- `flossi0ullk-consensus-gateway` — local consensus gateway, voter/provider rosters.

## Staleness policy

Use the probe's mtime fields:

- L0 older than 14 days → flag as potentially stale; check `INDEX.md` anyway.
- ADR older than relevant code edit → re-read the ADR; your model of canonical decisions may be wrong.
- `_reference/` entries have no freshness guarantee — they are a library, not a canon.
END_FILE references/entry-points.md
````

### Payload: `CHANGELOG.md` → target: `<skill-folder>/CHANGELOG.md`

````
BEGIN_FILE CHANGELOG.md
# Changelog

## 0.2.0 — 2026-04-22

### Added
- `scripts/orient_probe.py` — deterministic, stdlib-only, no-mutation probe script that emits a markdown (or JSON) orientation packet. Tested against happy, lock-present, cold-start, and JSON-mode paths.
- `references/entry-points.md` — the canonical-entry-point map referenced by v0.1.0 but not previously shipped.
- Step 0 probe as mandatory prelude to any canonical read.
- Token-budget tiers (T0/T1/T2/T3) with explicit caps.
- Failure ladder — per-artifact fallbacks when canonical files are missing.
- Manual probe ladder — shell-only fallback when `orient_probe.py` itself is absent.
- Self-audit checklist — five questions to answer before closing any task.

### Changed
- Tightened the Rules section: added "No broad opens", "Probe before read", and explicit ADR-gate on architecture/governance edits.
- Recast "load files in order" as "stop at the lowest tier that answers the task."

### Rationale
v0.1.0 was a checklist; an agent following it had to attempt-then-recover because nothing in the skill verified canonical files were present. That violated the skill's own stated purpose ("without spraying tokens"). v0.2.0 makes the probe step mandatory and deterministic, so token spend is known before any canon is read.

### Known gaps
- `[VERIFY]` tags in `references/entry-points.md` mark paths inferred from the skill's declarations and workspace conventions. Should be confirmed against the live repo.
- The probe assumes `context_router.py`'s interface is `python context_router.py <query> --format markdown --limit N`. If the real signature differs, adjust `try_router()`.
- Staleness threshold for L0 is hard-coded at 14 days. Move to a config file if multiple canons need different thresholds.
END_FILE CHANGELOG.md
````

### Payload: `scripts/orient_probe.py` → target: `FLOSS/scripts/orient_probe.py`

````
BEGIN_FILE scripts/orient_probe.py
#!/usr/bin/env python3
"""orient_probe.py — FLOSSI0ULLK orientation probe.

Emits a deterministic markdown packet describing which canonical artifacts are
present, fresh, and cheap to read. No mutation. No network. Stdlib only.

Designed to be the mandatory Step 0 of the flossi0ullk-orient skill. Run from
the repo root:

    python FLOSS/scripts/orient_probe.py --query "task in one line"

Exit codes:
    0  probe succeeded (packet emitted)
    2  probe ran but flagged a blocking issue (e.g. lock file present)
    3  invalid invocation

Output is intentionally compact (target: well under 500 tokens).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Canonical entry points declared by the orient skill. Keep in sync with
# references/entry-points.md.
CANONICAL_FILES: list[tuple[str, str, str]] = [
    # (path, tier, one-line purpose)
    (".agent-surface/context/CONTEXT_L0.md", "T1", "Cheap re-orientation context"),
    (".agent-surface/context/CONTEXT_L1.md", "T2", "Deeper re-orientation context"),
    ("INDEX.md", "T1", "Repo-root map"),
    ("FLOSS/CLAUDE.md", "T1", "Agent operating notes"),
    ("FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md", "T1*", "Governing principles (only if relevant)"),
    ("FLOSS/scripts/context_router.py", "T1.5", "Query -> corpus roots"),
    ("FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md", "T2", "Intake/filewatch arch"),
    ("FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md", "T2", "Filewatch metaharness plan"),
    ("FLOSS/scripts/watch_intake.py", "T2", "Intake watcher"),
    ("FLOSS/scripts/process_intake_events.py", "T2", "Intake event processor"),
]

EVENTS_DIR = ".agent-surface/events"
LOCK_GLOB = ".agent-surface/context"  # scan this dir for *.lock
STALENESS_DAYS_L0 = 14


@dataclass
class FileStatus:
    path: str
    tier: str
    purpose: str
    present: bool
    size: Optional[int] = None
    mtime: Optional[float] = None
    sha256_prefix: Optional[str] = None

    @property
    def age_days(self) -> Optional[float]:
        if self.mtime is None:
            return None
        return (time.time() - self.mtime) / 86400.0

    @property
    def stale_l0(self) -> bool:
        return (
            self.path.endswith("CONTEXT_L0.md")
            and self.age_days is not None
            and self.age_days > STALENESS_DAYS_L0
        )


def sha256_prefix(path: Path, *, nbytes: int = 1 << 20) -> str:
    """Return first 12 hex chars of sha256 over up to nbytes of file content."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(nbytes))
    return h.hexdigest()[:12]


def stat_file(path: Path, *, tier: str, purpose: str) -> FileStatus:
    rel = str(path)
    if not path.exists():
        return FileStatus(path=rel, tier=tier, purpose=purpose, present=False)
    try:
        st = path.stat()
        return FileStatus(
            path=rel,
            tier=tier,
            purpose=purpose,
            present=True,
            size=st.st_size,
            mtime=st.st_mtime,
            sha256_prefix=sha256_prefix(path),
        )
    except OSError as exc:
        return FileStatus(
            path=rel,
            tier=tier,
            purpose=f"{purpose} (stat error: {exc})",
            present=False,
        )


def events_queue_depth(root: Path) -> Optional[int]:
    events = root / EVENTS_DIR
    if not events.is_dir():
        return None
    try:
        return sum(1 for _ in events.iterdir())
    except OSError:
        return None


def lock_files(root: Path) -> list[str]:
    d = root / LOCK_GLOB
    if not d.is_dir():
        return []
    try:
        return sorted(p.name for p in d.iterdir() if p.suffix == ".lock")
    except OSError:
        return []


def try_router(root: Path, query: str, *, limit: int) -> tuple[bool, str]:
    """Run context_router.py if present. Return (ran_ok, captured_output)."""
    script = root / "FLOSS/scripts/context_router.py"
    if not script.is_file():
        return False, "router script not found"
    python = shutil.which("python3") or shutil.which("python")
    if python is None:
        return False, "no python interpreter on PATH"
    try:
        result = subprocess.run(
            [python, str(script), query, "--format", "markdown", "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"router invocation failed: {exc}"
    if result.returncode != 0:
        return False, f"router exited {result.returncode}: {result.stderr.strip()[:400]}"
    out = result.stdout.strip()
    # Keep the packet bounded — cap router output to ~40 lines.
    lines = out.splitlines()
    if len(lines) > 40:
        out = "\n".join(lines[:40]) + "\n... (truncated)"
    return True, out


def fmt_time(ts: Optional[float]) -> str:
    if ts is None:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts)) + "Z"


def render_markdown(
    *,
    query: str,
    statuses: list[FileStatus],
    queue_depth: Optional[int],
    locks: list[str],
    router_ran: bool,
    router_output: str,
) -> str:
    lines: list[str] = []
    lines.append("# FLOSSI0ULLK orientation packet")
    lines.append("")
    lines.append(f"- query: `{query or '(none)'}`")
    lines.append(f"- utc: `{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}`")
    if queue_depth is None:
        lines.append("- events queue: `(absent)`")
    else:
        lines.append(f"- events queue depth: `{queue_depth}`")
    if locks:
        lines.append(f"- **LOCKS PRESENT**: {', '.join(locks)} — wait before reading context.")
    lines.append("")
    lines.append("## Canonical artifacts")
    lines.append("")
    lines.append("| tier | present | age (d) | size | sha256 | path | note |")
    lines.append("| ---- | ------- | ------- | ---- | ------ | ---- | ---- |")
    for s in statuses:
        age = f"{s.age_days:.1f}" if s.age_days is not None else "-"
        size = f"{s.size}" if s.size is not None else "-"
        sha = s.sha256_prefix or "-"
        note_bits = []
        if s.stale_l0:
            note_bits.append(f"stale>{STALENESS_DAYS_L0}d")
        note = ",".join(note_bits) or s.purpose
        flag = "YES" if s.present else "MISSING"
        lines.append(f"| {s.tier} | {flag} | {age} | {size} | {sha} | `{s.path}` | {note} |")
    lines.append("")
    lines.append("## Router")
    lines.append("")
    if router_ran:
        lines.append("Ran. Output:")
        lines.append("")
        lines.append("```markdown")
        lines.append(router_output)
        lines.append("```")
    else:
        lines.append(f"Not run: {router_output}")
    lines.append("")
    lines.append("## Recommended reads (stop at lowest tier that answers the task)")
    lines.append("")
    present_by_tier: dict[str, list[str]] = {}
    for s in statuses:
        if s.present:
            present_by_tier.setdefault(s.tier, []).append(s.path)
    for tier in ("T1", "T1*", "T1.5", "T2"):
        if tier in present_by_tier:
            lines.append(f"- **{tier}**: " + ", ".join(f"`{p}`" for p in present_by_tier[tier]))
    if not present_by_tier:
        lines.append("- none of the declared canon is present — cold start; see entry-points.md.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="FLOSSI0ULLK orientation probe")
    parser.add_argument("--query", default="", help="One-line task description")
    parser.add_argument("--root", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--limit", type=int, default=4, help="Router result limit")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root not a directory: {root}", file=sys.stderr)
        return 3

    os.chdir(root)

    statuses = [
        stat_file(Path(p), tier=tier, purpose=purpose)
        for (p, tier, purpose) in CANONICAL_FILES
    ]
    queue_depth = events_queue_depth(root)
    locks = lock_files(root)
    router_ran, router_output = try_router(root, args.query or "orient", limit=args.limit)

    if args.json:
        payload = {
            "query": args.query,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "events_queue_depth": queue_depth,
            "locks": locks,
            "router": {"ran": router_ran, "output": router_output},
            "files": [
                {
                    "path": s.path,
                    "tier": s.tier,
                    "present": s.present,
                    "size": s.size,
                    "mtime": s.mtime,
                    "age_days": s.age_days,
                    "sha256_prefix": s.sha256_prefix,
                    "purpose": s.purpose,
                }
                for s in statuses
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            render_markdown(
                query=args.query,
                statuses=statuses,
                queue_depth=queue_depth,
                locks=locks,
                router_ran=router_ran,
                router_output=router_output,
            )
        )

    return 2 if locks else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
END_FILE scripts/orient_probe.py
````

---

## 8. Origin-session 5-box compliance check

```
[x] Intent echoed (handoff packet for local-session continuation)
[x] Evidence gate applied (NOW = bootstrap only; LATER gated on answers; NEVER list explicit)
[x] Anti-sycophancy: payloads labeled Unverified-against-live-repo; rejected alternatives logged with reasons
[x] Open questions carried forward and re-ask mandated (§5)
[x] Smallest-artifact + source-authority respected (one file; repo declared authoritative over packet)
```

*The protocol is the conversation. Verify, then build. — origin instance, 2026-06-09*
