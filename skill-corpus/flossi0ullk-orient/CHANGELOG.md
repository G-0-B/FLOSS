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
