# Patch note: CLAUDE.md — 2026-07-16

Two small, low-friction corrections. Both are find/replace edits, no structural change to the file. See `FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.3.md` §5 (C6, minor items) for full rationale and evidence.

---

## Patch 1 — Dev-plane substrate claim (C6)

**Find** (under "Current Operating Stack"):

```
- **Canonical dev-plane code substrate:** `Radicle` (see `docs/adr/ADR-8-radicle-dev-substrate.md`). GitHub remains a pragmatic mirror, not the architectural center.
```

**Replace with:**

```
- **Current dev-plane code substrate:** `GitHub` (`G-0-B/FLOSS`). Radicle (`docs/adr/ADR-8-radicle-dev-substrate.md`, Accepted, Specified — bridge unproven) is the sovereignty *target*, not the current fact — see `docs/governance/FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.3.md` §C2/§C6 for the reconciliation. Promote to canonical only after a successful mirror workflow and contributor-onboarding test.
```

**Why:** `FLOSSI0ULLK_CANONICAL_BUILD_SPINE_v0.2.md` (2026-07-02) already resolved this the other way — GitHub is current-canonical, Radicle is the target — but that resolution never propagated back into `CLAUDE.md`, which still states ADR-8's original proposal as settled fact. Since `CLAUDE.md` is the first orientation doc most agentic readers load, this was actively misleading anyone who read `CLAUDE.md` without also cross-checking the build spine.

---

## Patch 2 — ADR range (minor)

**Find** (under "Key Entry Points"):

```
current set per v2.0 suite is ADR-0, 0.1, 1–11; ADR-MCP-ORCHESTRATOR was assigned permanent number ADR-10; ADR-N (IPFS) was assigned ADR-11
```

**Replace with:**

```
current set per v2.0 suite is ADR-0, 0.1, 1–12; ADR-MCP-ORCHESTRATOR was assigned permanent number ADR-10; ADR-N (IPFS) was assigned ADR-11; ADR-12 (Consent Gate Protocol, 2026-05-19) is the newest addition — see `docs/adr/INDEX.md`
```

**Why:** `docs/adr/INDEX.md` (v2.0.0, 2026-05-25) already lists ADR-12 as active (`Draft (implementation-backed)`, high friction, `OVERRIDE FORBIDDEN`). `CLAUDE.md`'s summary line predates that addition.

---

## Not included in this patch (deliberately)

- The three-way license conflict (C7) and the SDD-spec dual-naming (C8) both touch `CLAUDE.md` (license footer, directory map / Key Entry Points) but require Anthony's explicit decision first — see build spine v0.3 §8 NOW items 9–10. Patching `CLAUDE.md` for those now would just create a fourth thing to reconcile later.
