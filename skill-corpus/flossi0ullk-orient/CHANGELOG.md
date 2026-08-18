# Changelog

## 0.3.4 — 2026-07-30

- Split classification hygiene into required project-input and documentation-example
  slots after injected pressure testing found a combined alternative omitted
  explicit Quick Start exclusion.

## 0.3.3 — 2026-07-30

- Added required Fact/Inference/Unknown and durable-write disposition slots to the
  mandatory response skeleton.
- Tightened nonzero-exit classification: absent output is `Unknown pending output`;
  expected check/drift requires observed output.

## 0.3.2 — 2026-07-30

- Moved the evidence, classification, and OmniRoute attempt/disposition templates
  into a mandatory high-salience response skeleton.
- Completion and any user-facing conclusion now depend on filled slots, including a
  disposition when requests are prohibited.

## 0.3.1 — 2026-07-30

- Refactored operational and OmniRoute guidance into required output slots after
  post-edit tests showed incomplete evidence envelopes and attempt/disposition
  records.
- Added compact nonzero-exit and documentation-example classification hygiene.

## 0.3.0 — 2026-07-30

- Added compact operational-claim contracts: functional-path probes,
  Fact/Inference/Unknown separation, complete evidence envelopes, durable-write
  readback, and manual OmniRoute fallback with attempt preservation, analog-vote
  validation, verified-provider distinction, and human `CONFLICT` escalation.

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
