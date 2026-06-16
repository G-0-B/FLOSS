---
id: project-holochain-0-7-migration-pending
type: project
created: '2026-05-26'
status: pending
applies_to:
- any-agent
title: M14 — Holochain 0.6 → 0.7-dev substrate migration is the next substrate work
---

## What's actually true

The next substrate-class work item is migrating from `holonix main-0.6` (hc 0.6.1, EOL upstream) to `holonix main-0.7-dev` so the existing `@holochain/tryorama` line pairs with the conductor and end-to-end DHT verification becomes earnable.

Plan + 7 sequential gates + rollback procedure live at [`docs/superpowers/plans/2026-05-26-holochain-0.7-migration.md`](../../superpowers/plans/2026-05-26-holochain-0.7-migration.md). Branch name reserved: `working/2026-05-26-holochain-0.7-migration` (off current stabilization-canon).

Operator-confirmed 2026-05-26 as option (a) of the M13 three-option fork.

## How to apply

- Do NOT start the migration without reading the plan first — it specifies snapshot/rollback discipline and per-gate verification order.
- Substrate blast radius — APPROVE ≥ 0.85, OVERRIDE FORBIDDEN per ADR-12. Provenance packet required on each substrate-class commit.
- ADR-13 ("Holochain 0.7-dev migration") drafted alongside the work, not after.
- Companion update needed: [`holochain-version-line-skew`](holochain-version-line-skew.md) memory once the pin lands.
- Sister project `FLOSSI_U/` — verify whether it depends on Holochain too before merging the migration anywhere shared.

## Why it matters

Two load-bearing truth-status claims are currently `NOT verified` because of the tooling gap (see [`tryorama-tooling-gap-2026-05-26`](tryorama-tooling-gap-2026-05-26.md)):

1. ADR-12 "consent Tryorama scenarios are locally verified" (corrected in commit `f4a70cf`)
2. MVP_PLAN "Holochain hApp/Tryorama integration tests pass" (corrected in commit `5969d09`)

M14 makes both earnable again.
