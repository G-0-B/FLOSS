---
id: project-gates-exempt-by-default
type: project
created: '2026-09-01'
status: active
applies_to:
- any-agent
source: gate-adoption-audit
title: Gates in this repo are exempt by default, so adoption decays while the gate still reports green
description: Accepted gates here are fail-closed inside an opt-in scope. ADR-18's reuse gate fires on 9 of 109 registered artifacts because an omitted tier is an exemption; ADR-18 itself is registered untiered. Measure gate COVERAGE, not just gate verdict.
---

# Gates are exempt by default

**Date:** 2026-09-01
**Status:** ✅ Verified — counts reproduced against `docs/specs/spec-registry.json` on `feat/coordination-room`
**Related:** [`installation-not-adoption.md`](installation-not-adoption.md), [`doc-explosion-acknowledged.md`](doc-explosion-acknowledged.md), [`scale-mismatch-is-the-recurring-defect.md`](scale-mismatch-is-the-recurring-defect.md)
**Packet:** `docs/reviews/2026-09-01-polyglot-plugin-materializer-spec/GATE-ADOPTION-AUDIT.md`

## The measurement

ADR-18 (Prior-Art and Reuse Gate) is Accepted, operator-approved 2026-07-16, and really implemented — `scripts/spec_gate.py:206` fails closed when a registry entry carries `"tier": 1|2` without a `reuse` block.

Its actual reach:

| | count |
|---|---|
| registered artifacts | 109 |
| tier 1 | 6 |
| tier 2 | 3 |
| no tier | 100 (43 grandfathered, 57 untiered and not grandfathered) |
| carrying a reuse block | 9 |

**The reuse gate fires on 8% of registered artifacts and on 0% of unregistered ones.** This is not a spec_gate bug. Its own failure message states the rule: *an omitted tier is an exemption, not a default*. The gate is fail-closed at the centre and fail-open at the boundary.

`docs/adr/ADR-18-prior-art-reuse-gate.md` is itself registered without a tier. The prior-art gate is exempt from the prior-art gate. So are ADR-13, 14, 15, 16, 17, 19.

## What it cost

`py-filelock` 3.18.0 was installed at `C:/Python313/Lib/site-packages/filelock/`, declared in no requirements file, while `packages/activity_log/filelock.py` was hand-written with msvcrt and fcntl branches and reviewed across ~40 rounds on the PR41 lineage. ADR-18 exists to catch exactly this and never fired, because the capability was never registered with a tier.

Per-surface caveat that must travel with that instance: py-filelock is the right reuse target for **process-lifetime** locks (materializer transaction, anchor publish). It is the **wrong** tool for the daemon claim, which must outlive its process — an OS lock is released on process death by definition. Reuse verdicts are per-surface; an undifferentiated adopt would break the daemon claim.

## Why it stays invisible

1. The gate is genuinely fail-closed, so running it *feels* like compliance.
2. Scope is opt-in through a field whose absence is an exemption.
3. Nothing measures coverage. The gate reports pass/fail on what it saw and never reports how little it saw.

Same shape as the aggregate-materializer fail-fast defect: `materialize_shared_agent_memory.py:199` raised on the first file missing frontmatter, took down all 62 memory projections on 2026-08-29, and went unnoticed until 2026-09-01 because the error named one file. **Both artefacts under-report their own blindness.**

## The standing rule

**Measure gate coverage, not just gate verdict.** Any gate that reports pass/fail must also report the size of the set it examined against the size of the set it could have examined. A gate with no coverage number is an unfalsifiable claim of compliance.

Corollary, and the reason this memory exists rather than a new skill: **the remedy for a forgotten surface is never an additional surface.** [`installation-not-adoption.md`](installation-not-adoption.md) already established that installation is not adoption — that rule was written about the reuse-ledger's `adapter_test` gate and never applied to our own gates. We recorded the lesson and then exempted ourselves from it. Adding a reminder mechanism to remember the reminder mechanisms extends the defect.

## How to apply

- Before proposing a new skill, hook, agent, or checklist to make an existing practice stick: check whether the practice already has a gate, and whether that gate has a coverage number. Fix the number first.
- When adding to `spec-registry.json`, set a tier. An omitted tier is a decision to exempt, so make it explicitly, with a reason.
- When a gate is habitually red (spec_gate `--check` exits 1 on this branch today: two unregistered hooks, one stale entry), treat that as demotion-to-log-line, not as a backlog item.
