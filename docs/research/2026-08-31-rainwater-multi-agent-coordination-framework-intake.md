# Rainwater multi-agent coordination framework — intake delta

**Date:** 2026-08-31  
**Status:** Research intake; no framework adoption  
**Truth status:** Mixed — source structure inspected locally; source case-study metrics are author-reported and not FLOSSI0ULLK measurements  
**Source:** `C:/~shit/timothyjrainwater-lab-multi-agent-coordination-framework-8a5edab282632443.md` (MIT-licensed gitingest snapshot)

## Why retain this delta

The source describes a practical multi-agent workflow derived from a D&D rules-engine project. It reports 8,521+ tests, 338 formulas, 100+ sessions, and a seven-agent dispatch in which three agents silently failed to commit. Those figures describe the source project only; they have not been independently reproduced here.

Most of the framework overlaps existing FLOSSI0ULLK practice, so importing its templates would create parallel governance. The useful output is a small comparison against existing surfaces.

## Existing coverage

| Source pattern | Existing FLOSSI0ULLK surface | Disposition |
|---|---|---|
| Durable, self-contained work orders | `docs/governance/uop-v2.1.md` plan/execute/trace gates | Adopt existing |
| Isolated concurrent work | Git worktrees + `docs/agent-memory/project/coordination-room-v0.md` path claims | Adopt existing |
| Machine-grounded context before action | `orient_probe.py`, `context_router.py`, source-authority ladder | Adopt existing |
| Verification after implementation | UOP VERIFY gate, named test commands, provenance packets | Adopt existing |
| Failure-derived process improvement | `2026-08-25-provenance-failure-mode-register.md` and review-loop learnings | Adopt existing |

## Candidate deltas

1. **Authority tagging.** When domain rules are contested, add a compact `SPEC | POLICY | UNSPECIFIED` field to the existing task brief rather than creating another authority catalog.
2. **Consume-site verification.** For data, config, or schema work, distinguish write/read success from proof that a real consumer observed the change. If no consumer exists, label it `CONSUME_DEFERRED`.
3. **Finding disposition.** Research and audit findings should carry `DISPATCHED`, `DEFERRED(date/reason)`, or `CLOSED(reason)` in the future machine-readable intake/retrieval index.
4. **Read-only periodic audits.** Retain the pattern, but do not adopt a fixed cadence without local evidence that the cadence pays for itself.

## Rejected transfers

- Do not import project-specific roles, paths, templates, cadence, or percentage guarantees.
- Do not treat every file containing a fact as equally authoritative; FLOSSI0ULLK has a strict source-authority ladder.
- Do not replace shared memory with protocol alone; Plane A memory remains useful but subordinate to repository canon.
- Do not generalize the source project's case-study metrics into FLOSSI0ULLK benchmarks.

## Disposition

The full source is preserved as raw intake at `docs/research/intake_raw/2026-08-31-root/reports/timothyjrainwater-lab-multi-agent-coordination-framework-8a5edab282632443.md`. This delta is the retrieval-facing comparison; neither artifact changes project architecture by itself.
