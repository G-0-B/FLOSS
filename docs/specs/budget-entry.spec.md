# BudgetEntry Specification

**Version:** 1.0.0
**Status:** Specified
**Truth Status:** Specified (code exists in integrity/coordinator zomes; not yet compiled/validated)
**Last Updated:** 2026-03-05

---

## 1. Purpose

A `BudgetEntry` tracks an agent's resource usage within a time window. It implements the Autonomy Kernel's "resource-bounded autonomy" concept from the VVS spec — agents have a finite budget of Resource Units (RU) per time window, preventing any single agent from overwhelming the network.

---

## 2. Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent` | AgentPubKey | Yes | The agent whose budget this tracks |
| `remaining_ru` | f32 | Yes | Remaining Resource Units in current window |
| `window_start` | Timestamp | Yes | Start of the current budget window |

---

## 3. Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `BUDGET_PER_WINDOW` | 100.0 RU | Total budget per window |
| `BUDGET_WINDOW_SECS` | 86400 (24h) | Window duration in seconds |
| `COST_ADD_KNOWLEDGE` | 33.0 RU | Cost to create a RoseNode |
| `COST_LINK_EDGE` | 3.0 RU | Cost to create a KnowledgeEdge |
| `COST_CREATE_THOUGHT_CREDENTIAL` | 10.0 RU | Cost to create a ThoughtCredential |

---

## 4. Invariants

1. **INV-BE-001:** `remaining_ru` MUST be >= 0.0
2. **INV-BE-002:** An operation MUST be rejected if its cost exceeds `remaining_ru`
3. **INV-BE-003:** Budget resets to `BUDGET_PER_WINDOW` when current time exceeds `window_start + BUDGET_WINDOW_SECS`

---

## 5. Behavior

```
CONSUME_BUDGET(agent, cost):
  budget = GET_OR_CREATE_BUDGET(agent)
  IF current_time > budget.window_start + BUDGET_WINDOW_SECS:
    budget.remaining_ru = BUDGET_PER_WINDOW
    budget.window_start = current_time
  IF cost > budget.remaining_ru:
    REJECT "Budget exceeded"
  budget.remaining_ru -= cost
  SAVE budget
```

---

## 6. Implementation Reference

- **Integrity zome:** `ARF/dnas/rose_forest/zomes/integrity/src/lib.rs` (BudgetEntry struct)
- **Coordinator zome:** `ARF/dnas/rose_forest/zomes/coordinator/src/budget.rs` (consume_budget, get_budget_state)

---

## 7. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-05 | Initial specification extracted from coordinator zome code |
