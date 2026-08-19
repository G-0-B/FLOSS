# Intake Event Specification

**Version:** 0.1.0
**Status:** Specified
**Truth Status:** Specified
**Last Updated:** 2026-04-19

## 1. Purpose
An `IntakeEvent` is a normalized file-change record emitted by the filewatch
metaharness skeleton.

It exists so observers, consolidators, and future MCP surfaces can exchange
change information without hand-parsing filesystem churn.

## 2. Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String | Yes | Unique event identifier |
| `observed_at` | Timestamp | Yes | ISO 8601 UTC timestamp |
| `event_type` | Enum | Yes | One of `created`, `modified`, `deleted` |
| `watch_domain` | Enum | Yes | One of `root-intake`, `canon`, `shared-surface`, `traces`, `agent-surface`, `other` |
| `source` | String | Yes | Emitting watcher or pipeline identifier |
| `abs_path` | String | Yes | Absolute file path |
| `rel_path` | String | No | Workspace-relative path when applicable |
| `corpus_hint` | String | No | Suggested routing corpus |
| `size_bytes` | Integer | No | File size when the file still exists |
| `mtime_ns` | Integer | No | Last modification timestamp in nanoseconds |
| `sha256` | String | No | Content hash when available |

## 3. Invariants

1. `observed_at` MUST be ISO 8601
2. `event_type` MUST be one of `created`, `modified`, `deleted`
3. `watch_domain` MUST use the shared domain vocabulary
4. `abs_path` MUST be non-empty
5. `sha256`, when present, MUST be a 64-character lowercase hex string

## 4. Notes
- `deleted` events may omit `size_bytes`, `mtime_ns`, and `sha256`
- `corpus_hint` is advisory, not authoritative
- this event is queue-level provenance, not canonical truth by itself
- queue consumers MUST treat `IntakeEvent` files as append-only runtime artifacts
- sidecars that emit memory or shadow observations MUST emit events first and MUST
  NOT mutate canon directly
- append-only shadow logs (for example future `.jsonl` file shadows) are inputs to
  curation and promotion, not substitutes for ADRs or other canonical decisions
