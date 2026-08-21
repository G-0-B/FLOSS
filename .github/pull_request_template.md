## What and why

<!-- What changes, and what it is for. One or two paragraphs. -->

## Scope

<!--
Keep this honest. A PR that touches 300 files because it inherited them is a PR
nobody can review, and its review will be dominated by findings in code it did
not write. If that is what happened, say so here and say which files are the
actual change.
-->

- Files actually changed by this work:
- Files touched only incidentally (merges, renames, formatting):

## Truth status

<!--
Per the ADR suite: ✅ Verified / ⚠️ Specified / 🔮 Aspirational / ❌ Blocked.
No claim ships as ✅ Verified without a traceable repo artifact behind it.
-->

| Claim | Status | Evidence |
|---|---|---|
|  |  |  |

## Prior art and reuse (ADR-18)

- [ ] Reuse gate considered: **adopt / extend / compose / build** — verdict:
- [ ] `compose` or `build` verdict has at least one direct probe recorded
- [ ] Tier 2 change has an adversarial reuse review (≥3 provider surfaces, ≥3 model families)
- [ ] Not applicable — why:

## Tests

- [ ] The green set passes locally. This is the exact invocation the required
      `green-set` job runs; the deselection is the one known-red test recorded
      in `.github/workflows/python-ci.yml`, so the plain three-directory command
      exits nonzero even on an unchanged baseline:

      ```
      python -m pytest packages/ tests/ scripts/tests/ \n        --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
      ```
- [ ] New behaviour has a test that fails without the change
- [ ] Green set in `.github/workflows/python-ci.yml` unchanged, or widened (never narrowed)

Result:

```text
<!-- paste the pytest summary line -->
```

## Docs and registries

- [ ] `INDEX.md` updated if a canonical document moved or was added
- [ ] New spec has both `.schema.json` and `.spec.md` in `docs/specs/`, and a `spec-registry.json` entry
- [ ] Architecture decision has an ADR
- [ ] Superseded canonical docs went to `archive/` — never deleted, and raw intake never archived

## Risk

- Blast radius: <!-- Local / Module / System / Substrate -->
- Rollback plan:
