---
id: project-provenance-audit-doctor
type: project
status: active
applies_to:
  - FLOSSI0ULLK
  - provenance
  - shared-surface
---

# Provenance Audit Dispositions And Shared-Surface Doctor

As of 2026-05-25, provenance packet validation and operator audit disposition
are intentionally separate.

`packages/activity_log/provenance.py::validate_packet()` remains strict: current
artifact hashes must match, signatures must verify, and governed-claim evidence
must not rely on stale packets.

`scripts/audit_provenance_packets.py` now classifies daily audit records as
`valid`, `superseded`, or `invalid`. Superseded means historical packet evidence
is preserved but no longer current truth, such as mutable generated projection
drift or older packet content covered by newer valid packet evidence.

The umbrella shared-surface materializer now has a read-only doctor mode:

```powershell
python FLOSS/scripts/materialize_shared_agent_surface.py --workspace-root C:\~shit --doctor
```

It reports shared-surface drift, harness roster counts, agentmemory health,
heartbeat STOP state, and provenance audit counts in one command. A nonzero exit
means operator attention is still needed.
