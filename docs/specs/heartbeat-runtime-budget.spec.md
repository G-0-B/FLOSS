# Heartbeat Runtime Budget Spec

**Status:** ⚠️ Specified  
**Date:** 2026-05-19  
**Scope:** `FLOSS/scripts/heartbeat.py`, `FLOSS/scripts/poll_high_roi_actions.py`, voter-profile usage, and generated runtime surfaces under `.agent-surface/heartbeat/`.

## Problem

The heartbeat loop was running `poll_high_roi_actions.py` on every tick with a high-diversity voter roster. At a 10-minute cadence, that can burn provider daily token budgets even when the slate has not changed. This degrades the actual consensus gateway because rate-limited voters later return neutral/error votes instead of substantive independent judgments.

## Runtime Policy

1. Cheap local work may run every heartbeat tick:
   - `process_intake_events.py`
   - `heartbeat_slate.py`
2. Consensus polls are not cheap local work. They must pass all gates:
   - daily round cap has enough headroom for the expected poll cost;
   - high-ROI slate signature differs from the last polled signature, or a periodic confirmation interval has elapsed;
   - no STOP file is present.
3. Groq-backed autonomous synthesis must pass a staging-queue backpressure gate before creating more drafts.
4. Routine heartbeat polls use `balanced` by default.
5. `diverse-max` is reserved for explicit human-requested consensus, manual claim validation, or a slow periodic sweep with a nonzero confirmation interval.
6. Round accounting must use the actual poll result count when available. It must not silently return zero because a work item name includes a profile suffix.
7. Each skipped poll or synthesis pass must log the reason to `.agent-surface/heartbeat/ticks.log`.
8. Every poll execution must append a global `Action` record to `.agent-surface/activity.jsonl` through `poll_high_roi_actions.py`.

## Defaults

| Setting | Default | Rationale |
|---|---:|---|
| `FLOSS_HEARTBEAT_PROFILE` | `balanced` | Keeps routine checks cheap. |
| `FLOSS_HEARTBEAT_WIDE_PROFILE` | `diverse-max` | Preserves a manual/periodic breadth option. |
| `FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS` | `72` | At a 10-minute cadence, wide sweeps can occur at most about every 12 hours. |
| `FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS` | `72` | At a 10-minute cadence, unchanged slates are reconfirmed about every 12 hours. |
| `FLOSS_DAILY_ROUND_CAP` | `40` | Eight 5-candidate polls/day maximum unless overridden. |
| `FLOSS_HEARTBEAT_DISABLE_POLLS` | unset/false | Emergency full poll stop without stopping cheap local heartbeat work. |
| `FLOSS_SYNTHESIS_STAGING_CAP` | `25` | Do not create more Groq-backed synthesis drafts when review is already backed up. |
| `FLOSS_HEARTBEAT_DISABLE_SYNTHESIS` | unset/false | Emergency synthesis stop without stopping cheap local heartbeat work. |

## Non-Goals

- This spec does not change ADR-10 vote semantics.
- This spec does not remove `diverse-max`.
- This spec does not promote heartbeat outputs to canon. Heartbeat remains Plane A unless a separate claim/ADR path promotes an artifact.

## Acceptance Tests

- Routine rotation uses `balanced` for `poll_high_roi_actions.py`.
- A profile-qualified poll work item still counts rounds correctly.
- An unchanged slate is skipped before spending voter calls.
- A changed slate schedules a poll and stores enough state to skip repetition.
- The default wide-sweep cadence does not use `diverse-max` every two hours.
- Autonomous synthesis is skipped when the staging queue is at or above cap.
- Materialized runtime docs explain how to halt, resume, inspect, and budget the heartbeat.
