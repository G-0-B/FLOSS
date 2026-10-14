---
id: "provenance-packet-spec-v1.5-delta"
version: "1.0.0"
kind: "spec_delta"
status: "Proposed"
date: "2026-08-04"
target: "FLOSS/docs/specs/provenance-packet.spec.md (v1.4) + provenance-packet.schema.json"
supersedes: []
relates_to:
  - "ADR-12 (Consent Gate Protocol) — BLOCKS D1"
  - "ADR-15 (author-provenance binding, integrity zome) — complementary plane, no conflict"
  - "ADR-18 (Prior-Art & Reuse Gate) — this delta owes a Tier 2 reuse block"
  - "ADR-19 (OmniRoute) — its deferred ratification is the evidence for D1"
truth_status: "specified"
blast_radius: "System"
friction_tier: "high"
generator: "claude-opus-5 (adversarial/verification role)"
rollback_plan: "Delete this file. v1.4 spec remains authoritative and unchanged."
license: "AGPL-3.0-or-later (per ADR-7)"
---

# Provenance Packet v1.5 — Delta Proposal

**This is an edit-set against the repo's v1.4 spec, not a replacement.** v1.4 is
authoritative. Corrections edit the original; parallel specs are the failure mode
that produced a 25KB adversarial review orbiting a 20KB artifact, forever unmerged.

**Retracted from the external v1.4 draft before proposing anything:** its SAID
algorithm was wrong. It computed the `v` byte length with `sigs = []`, then
populated `sigs` afterward (~+92 bytes), so `v` could never match final canonical
bytes. The repo's 7-step algorithm — dummy `sigs = ["0B" + "A"*86]` before the
length pass — is correct. Also retracted: a two-state stale/tampered audit model,
strictly weaker than the repo's `valid | superseded | invalid` trichotomy.

---

## D1 — Bootstrap exemption for the governed gate `[+1, blocked on ADR-12]`

### Evidence (Verified, from ADR-19, 2026-07-26)

- 105 packets in `.agent-surface/provenance/`; **zero** carry a `consent_ref`.
- `entry_has_consent()` checks only that `decision_action_hash` is a non-empty
  string. It never resolves the hash.
- ADR-19 — **Accepted**, operator-consented, System radius — had its consensus
  ratification **deferred** because the claim fails closed with
  `E_GOVERNED_PROVENANCE_REQUIRED` and no `consent_ref` convention exists.
- ADR-19 records: *"Do not re-attempt this claim until ADR-12 defines how consent
  decisions are recorded and addressed."*

### The defect, stated plainly

The gate is **simultaneously too strict and vacuous.** Too strict: it blocks a
legitimate, operator-consented, evidence-complete ADR. Vacuous: any non-empty
string satisfies it, so it provides no actual guarantee. A gate that blocks
honest work while admitting arbitrary values is worse than no gate — it produces
the *appearance* of provenance enforcement plus a real obstruction.

### Proposed edit to §"Governed Boundary"

Add:

> **Bootstrap exemption.** Until ADR-12 defines `ConsentDecision` recording and
> addressing, `PROVENANCE_BOOTSTRAP=1` downgrades the `consent_ref` requirement
> to warn-only. When active it MUST emit a loud audit record naming the claim,
> and MUST NOT be default-on. Removal of the exemption is gated on ADR-12
> acceptance and is a v1.6 requirement.
>
> **Resolution requirement (fail-closed, post-ADR-12).** Once ADR-12 lands,
> `entry_has_consent()` MUST resolve `decision_action_hash` against the source
> chain and verify the referenced `ConsentDecision` exists, is authored by an
> agent authorized for the blast radius, and has `scope_granted ⊇` the claim's
> required scope. A non-empty string MUST NOT satisfy the gate.

**Sequencing.** D1's exemption half is shippable now and unblocks ADR-19. Its
resolution half is blocked on ADR-12. Do not ship the resolution before ADR-12 or
governance locks harder.

---

## D2 — Multisig headroom `[+1, low cost]`

Schema pins `sigs` to `minItems: 1, maxItems: 1`. KERI is multisig-native (`kt`
threshold, `k` key list), and the stated migration target is KERI-shaped. A hard
cap of one signature makes any future threshold-signing scheme a breaking schema
change.

**Edit:** `"maxItems": 1` → remove; keep `minItems: 1`. Spec text: *"v1.5 requires
exactly one signature; the array form is retained so threshold signing is additive."*

Zero implementation change today. Removes one future migration.

---

## D3 — Evidence-type extension `[+1]`

Schema enum: `spec | test | adr | url | commit | provenance_packet` (6).
`EvidenceRef` in `packages/orchestrator/claim_schema.py` is a frozen dataclass
with a `frozenset` — extension is a one-line change, no migration, no version bump.

**Edit:** add `file`, `log`, `activity`, `source_chain`.

**Rationale:** ADR-19's own evidence table cites commits, live smoke runs,
`scripts/smoke_test_voters.py` output, and a claim UUID. Under the current enum
those are unrepresentable as typed evidence and get flattened into `url` or prose.
Non-packet DAG roots are required by §"Recursion Semantics"; a wider root
vocabulary makes that requirement satisfiable honestly.

---

## D4 — Truth-label scope and the `Refuted` state `[+1]`

Two gaps, both surfaced by use rather than design.

**D4a — no branch scope.** `Verified` without a branch identifier is a claim about
an unnamed snapshot. Documented instances: OVCA v0.1 labelled the provenance layer
"✅ Verified — 145/145 tests" while pinning a `main` SHA that predated the code; a
later verification pass claimed `provenance.py` was absent from `main` while
reading a stale local ref. Both wrong, opposite directions, same cause.

**Edit:** every `Verified` claim carries `verified_on: <ref>@<commit>`. Applies to
spec headers, ADR truth-status blocks, and `a[].truth_status` where the claim is
about repo state.

**D4b — no `Refuted` value.** The enum (`Verified | Specified | Aspirational |
Unverified`) cannot express *checked and found false*. `Unverified` means nobody
looked. Filing refutations there loses the most actionable epistemic state in the
system. Live examples needing it: KERI-additive-migration (false — `t="prov"` is
not a registered ilk, KERI does not use RFC 8785/JCS, translation required
regardless); "Holochain Phase 0 complete" (native tests pass, harness does not run).

**Edit:** add `Refuted` to the kernel §4 enum via ADR. Permit `mixed` on composite
artifacts only with a `truth_status_breakdown` map. This is a kernel change
(friction_tier high) — route through the gate, do not land silently.

---

## D5 — Key-loss and threat-model honesty `[+1, docs only]`

**Edit, add to §"SAID And Signature Algorithm":**

> **Threat model.** In the pilot topology the signing key and the signed artifacts
> live under the same uid on the same machine. Any process that can write the
> artifacts can read the key and sign. Ed25519 here buys *shape* — future rotation,
> remote verification, KERI migration — not present-day resistance to a local
> attacker. Do not describe v1.5 as providing non-repudiation.
>
> **Key loss / compromise.** No rotation exists. On loss or compromise: generate a
> new `i`, start a new chain at `s=0`, `p=null`, and cite the last packet of the
> retired chain via `evidence_refs[type=provenance_packet]`. Record the transition
> in canon. This is documented degradation, not recovery. Rotation is deferred to
> the KERI-integration ADR.
>
> **`created_at` is self-asserted.** No trusted timestamping. Backdating is
> possible; `s` orders within a chain only. Packets are weak evidence for
> "who knew what when."

---

## D6 — Algorithm simplification `[0, optional]`

Steps 2–3 compute a `d` that step 5 discards. Since `d` is fixed-width 44 either
way, the step-2/3 digest serves only as a length proxy and is unnecessary — set
`d = "#"*44` and dummy `sigs` directly, compute `v`, then compute the real `d`.

Not a bug. Flagged only because a reader implementing from the text may wonder
whether the first digest is load-bearing. Either fix the steps or add a note.

---

## ADR-18 Reuse Block (required — this delta is Tier 2)

```yaml
capability: "Signed, walkable, content-addressed provenance records for per-edit AI agent actions, with governed consent gating"
search_date: "2026-08-04"
candidates:
  - name: "in-toto attestations (ITE-6)"
    truth_status: "verified"
    note: "Signed statement/subject/predicate envelope; substrate under SLSA + Sigstore. Predicate type is extensible — a FLOSSI0ULLK predicate is expressible."
    gap: "Targets build artifacts, not per-edit agent actions. No per-agent sequence chain (s/p). No consent-gate concept."
  - name: "SLSA provenance"
    truth_status: "verified"
    note: "v1.0 'Distributing provenance' explicitly recommends sidecar files named from the artifact — same shape as .agent-surface/provenance/."
    gap: "Build-centric; assumes a builder identity, not an agent-per-edit identity."
  - name: "Sigstore / Cosign + Rekor"
    truth_status: "verified"
    note: "Keyless signing + transparency log."
    gap: "Requires external transparency-log dependency; conflicts with offline/local-first and Holochain-native operation."
  - name: "C2PA"
    truth_status: "verified"
    note: "Content provenance; recognized in California AB 853. EU AI Act Art. 50 enforceable 2026-08-02."
    gap: "Media-asset oriented; not source-chain or consent-gate shaped."
  - name: "KERI / keripy (Saider, Matter, Indexer)"
    truth_status: "verified"
    note: "CESR codes D/B, E, 0B and the 44-char '#' SAID placeholder confirmed against keripy coring.py. Field conventions adopted."
    gap: "t='prov' is not a registered ilk; KERI does not use RFC 8785/JCS. Migration is NOT additive — refutes the original rationale."
verdict: "extend"
verdict_rationale: >
  This delta extends the existing repo v1.4 spec; it builds nothing new. The
  underlying v1.4 format itself carries an UNPAID Tier 2 obligation (grandfathered
  2026-06-12, no tier, no reuse block) — its bespoke-vs-in-toto verdict was never
  probed. That audit is owed separately and should be recorded as a gate-miss trace.
irreducible_delta: >
  Testable: per-agent monotonic sequence with prior-digest continuity (s/p),
  consent-gated governed bindings resolvable against a Holochain source chain, and
  offline operation with no external transparency log. If an in-toto predicate can
  carry all three with a probe demonstrating it, the bespoke envelope should be
  retired in favor of an in-toto predicate type.
probe_required: true
probe_status: "NOT RUN — blocking for any future 'build' verdict on the envelope format"
emergency: false
```

---

## Registry and gate obligations surfaced

Findings from `spec-registry.json` v0.1.0 (`updated: 2026-06-12`):

1. **91 of 92 entries carry no reuse block.** Only `reuse-gate.spec` does. ADR-18
   is adopted and effectively unapplied. Either backfill tiers for
   architecture-class entries or record the coverage gap honestly — ADR-18's own
   falsifiers (<5 uses in ~6 months, verdict-changed rate ≈ 0) are approaching.
2. **`provenance-packet.spec.md` is grandfathered, untiered.** It is
   architecture-class → Tier 2 → owes an adversarial reuse review. See the
   `verdict_rationale` above.
3. **Registry `updated` field is stale** — says `2026-06-12` but contains
   `2026-07-16` ADR-18 registrations. Same drift class as everything else this week.
4. **`gated_surfaces` = `FLOSS/scripts`, `FLOSS/docs/specs`, `FLOSS/docs/adr`.**
   `ARF/**` is ungated, and its root holds loose docs (`ADR-0`, `ADR-1`,
   `ADR-N-spec-driven-development`, `PHASE_5_*`, `ARCHITECTURE_OVERVIEW`,
   `INTEGRATION_*`) plus three `.zip` archives. Either gate `ARF/docs` or move
   those into `FLOSS/docs` — currently they can drift without any gate firing.
5. **`.env` sits at repo root (~4.5 KB) and appears in the tree listing.** Keys
   reported rotated. Confirm it is gitignored and absent from history:
   `git log --all --oneline -- .env` and `git check-ignore -v .env`.

---

## Sequencing

| # | Action | Blocked by | Radius |
|---|---|---|---|
| 1 | D2, D3, D5, D6 — additive, docs + one frozenset line | — | Module |
| 2 | D1 exemption half — unblocks ADR-19 ratification | — | System |
| 3 | ADR-15 implementation — `BudgetEntry` returns unconditional `Ok(Valid)`; Semgrep HIGH; any agent can mint a budget entry naming any agent | cargo test + review | Substrate |
| 4 | ADR-12 consent anchoring — the true critical path | design | Substrate |
| 5 | D1 resolution half — fail-closed hash resolution | ADR-12 | System |
| 6 | D4 — kernel §4 enum change | ADR | Substrate |
| 7 | in-toto probe — pays the Tier 2 debt | — | Module |

**ADR-12 is the keystone.** It blocks D1's resolution half, ADR-19's ratification,
and the meaningfulness of every governed binding. ADR-15 is the highest-severity
*security* item (unvalidated `BudgetEntry`, author-spoofable `ThoughtCredential`).
Neither is a provenance-packet-format question, which is where four review rounds
went.
