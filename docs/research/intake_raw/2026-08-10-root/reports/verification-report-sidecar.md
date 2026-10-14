# Sidecar: UpgradableArtifact Header + Provenance Packet
### for `provenance-spine-v1.4-verification-report`

Prepend Part 1 to the report, or keep this file adjacent to it. Part 2 is a packet
skeleton ready to be signed by the already-merged `packages/activity_log/provenance.py`.

---

## Part 1 — UpgradableArtifact Header

```yaml
id: "provenance-spine-v1.4-verification-report"
version: "1.0.0"
kind: "verification_report"
status: "Accepted"
updated: "2026-07-30"
supersedes: []
truth_status: "mixed"          # NOT a kernel enum value — see schema note below
truth_status_breakdown:
  verified: >
    Part B B1-B4, B7, B8 (keripy coring.py, RFC 8785, PyPI).
    Part A items 1-6, 8, 10 (file contents, single reader pass).
  refuted: >
    Part B B5-B6: t="prov" is not a registered KERI ilk; the
    "additive migration to real KERI" rationale is FALSE.
    Part A: the v1.4 greenfield assumption is FALSE — the spine is already merged.
    CORRECTION 2026-08-04: the spine is on origin/main via PR #36
    (merged 2026-06-16), NOT merely on a working branch. An intermediate
    claim that provenance.py was absent from main came from a stale local
    main ref and was itself wrong. PR #38 is docs-only and stacked cleanly
    on #36 (merge-base --is-ancestor = 0).
  specified: "consent_integrity end-to-end deployment; repo-claimed test pass counts"
  unverified: >
    PR #38 in its entirety (robots-blocked); RUNTIME_SURFACES.md;
    METAHARNESS_OPERATING_MODEL.md; materializer --check; Action record volume;
    identity zome symbols; per-package dependency pins.
evidence_sources:
  - "G-0-B/FLOSS branch main — file contents via repository reader (single pass, not re-fetched)"
  - "G-0-B/FLOSS PR #25 (merged 2026-06-16) — rendered HTML"
  - "WebOfTrust/keripy src/keri/core/coring.py — MtrDex, Codes, Ilkage tables"
  - "IETF draft-ssmith-said; ToIP KERI specification"
  - "RFC 8785; PyPI: rfc8785, jcs, jsoncanon, blake3"
  - "SLSA v1.0 Distributing Provenance; in-toto ITE-6; C2PA"
upgrade_path: >
  Supersede when PR #38 is retrieved under authenticated access, or when a live CI run
  replaces self-reported test counts.
rollback_plan: "N/A — report is evidence, not a mutation. Discard and re-run if repo state moved."
friction_tier: "low"
license: "AGPL-3.0-or-later"
```

### Schema note — worth a kernel amendment

`truth_status: "mixed"` is **not** in the Master Metaprompt v1.3.1 §4 enum
(Verified | Specified | Aspirational | Unverified). Two real gaps surfaced by trying to
label this document honestly:

0. **No branch scope.** The single largest gap, and the cause of four wrong
   claims in one session. `Verified` with no `verified_on: branch@commit` is
   not verified — it is a claim about an unnamed snapshot. Every truth label
   should carry scope.
1. **No composite value.** A verification report carries heterogeneous claims by nature.
   Forcing one label either overclaims (Verified, while PR #38 is unretrieved) or
   underclaims (Unverified, while six KERI codes are confirmed against keripy source).
2. **No value for "actively disproven."** `Unverified` means *no evidence*. But B6 and the
   greenfield assumption were **checked and found false** — a stronger and more actionable
   state than absence of evidence. The current enum cannot express it, which means refutations
   get filed under the same label as things nobody looked at. That is a real information loss
   in a system whose whole purpose is evidence discipline.

Proposed v1.3.2 amendment: add **`Refuted`** to the enum; permit `mixed` on composite
artifacts **only** with an accompanying `truth_status_breakdown`. Until that ADR lands,
treat this header as a documented deviation, not precedent.

---

## Part 2 — Provenance Packet (unsigned skeleton)

Kernel §8: *no provenance packet → treat as context, not an actionable artifact.* Until
signed, this report is formally context. Fields conform to `provenance-packet.spec.md` §2.

`d` carries the 44-`#` SAID placeholder; `i`/`s`/`p` are null and `sigs` empty because
signing requires the local Ed25519 identity and `.chain.json` head state on your machine.
Populate by running the merged implementation:

```python
from packages.activity_log import provenance as prov
ident = prov.load_or_create_identity()
pkt = prov.create_packet(identity=ident, entries=[ ... ])   # entries from a[] below
```

```json
{
  "v": "FLOSSI10JSON000000_",
  "t": "prov",
  "d": "############################################",
  "i": null,
  "s": null,
  "p": null,
  "a": [
    {
      "claim_type": "observed_fact",
      "truth_status": "mixed",
      "created_at": "2026-07-30T00:00:00Z",
      "source_systems": [
        "claude-opus-5",
        "anthropic-advanced-research-subagent",
        "github:G-0-B/FLOSS@main",
        "github:WebOfTrust/keripy",
        "ietf:draft-ssmith-said",
        "rfc:8785",
        "pypi"
      ],
      "human_collision_node": "anthony",
      "action_ref": null,
      "consent_ref": null,
      "consent_payload_ref": null,
      "artifact_refs": [
        { "path": "provenance-spine-v1.4-verification-report.md", "sha256": null },
        { "path": "provenance-packet.spec.md", "sha256": null },
        { "path": "provenance-packet.schema.json", "sha256": null }
      ],
      "evidence_refs": [
        { "type": "file",   "ref": "packages/activity_log/provenance.py", "sha256": null },
        { "type": "file",   "ref": "packages/metacoordinator_mcp/tools.py", "sha256": null },
        { "type": "file",   "ref": "packages/orchestrator/claim_schema.py", "sha256": null },
        { "type": "file",   "ref": "packages/activity_log/schema.py", "sha256": null },
        { "type": "file",   "ref": "scripts/hook_post_write.py", "sha256": null },
        { "type": "file",   "ref": "ARF/dnas/rose_forest/zomes/consent_integrity/", "sha256": null },
        { "type": "spec",   "ref": "docs/specs/provenance-packet.spec.md", "sha256": null },
        { "type": "adr",    "ref": "ADR-12-consent-gate-protocol", "sha256": null },
        { "type": "commit", "ref": "G-0-B/FLOSS PR#25 merged 2026-06-16", "sha256": null },
        { "type": "url",    "ref": "https://github.com/WebOfTrust/keripy/blob/main/src/keri/core/coring.py", "sha256": null },
        { "type": "url",    "ref": "https://datatracker.ietf.org/doc/html/draft-ssmith-said", "sha256": null },
        { "type": "url",    "ref": "https://www.rfc-editor.org/rfc/rfc8785", "sha256": null },
        { "type": "url",    "ref": "https://slsa.dev/spec/v1.0/distributing-provenance", "sha256": null }
      ],
      "summary": "Verification of Provenance Spine v1.4 against repo state and primary sources. Two central assumptions refuted: (1) greenfield — a KERI-shaped provenance subsystem, evidence-bearing submit_claim with governed hard-block, extended EvidenceRef, and provenance-aware Action already exist on main; (2) additive KERI migration — t='prov' is not a registered ilk and KERI does not use JCS, so translation is required regardless. CESR codes D/B, E, 0B and the 44-char '#' SAID placeholder are confirmed against keripy. PR #38 unretrievable (robots-blocked). consent_integrity passes 10/10 native tests but has no working Tryorama path (blocker M13), so the governed hard-block is a live self-lockout risk.",
      "risks": [
        "Re-implementing a merged subsystem — v1.4 must become a diff, not a build",
        "Governed hard-block self-lockout while consent conductor path is broken (M13)",
        "Part A rests on a single unre-fetched reader pass; spot-check before implementing",
        "rust-ci.md does not execute — claimed Rust test passes are unenforced",
        "jcs 0.2.1 is minimally maintained; canonicalization drift silently invalidates all prior signatures",
        "Bespoke FLOSSI10JSON format forgoes in-toto/SLSA/Sigstore verifier interop"
      ],
      "benefits": [
        "Refutes greenfield assumption before implementation effort is spent",
        "Six CESR/KERI codes now Verified against primary source, not inferred",
        "Locates the consent self-lockout in a specific named blocker (M13) with a flip threshold",
        "EvidenceRef extension confirmed as a one-line frozenset edit, no migration",
        "Surfaces two kernel §4 enum gaps: no Refuted value, no composite value"
      ],
      "next_action": "Read the five merged files above; reframe v1.4 as a diff against main; resolve PR #38 under authenticated access; sign this packet as the genesis record.",
      "keri_event_ref": null,
      "a2a_entity_card_ref": null,
      "in_toto_predicate_type": null,
      "prov_o_activity_id": null
    }
  ],
  "sigs": []
}
```

---

## Why this is the better genesis packet

The v1.4 test plan proposed encoding *the v1.4 plan itself* as the genesis packet. That
tests serialization against a document with no real artifact hashes, no cross-system
sources, and no external evidence — a self-referential smoke test.

This report is a genuine cross-agent handoff: a research subagent and multiple primary
sources fed into a report that refutes two load-bearing claims and names a next action.
It has real files to hash, real URLs to cite, and a mixed truth status that exercises the
`truth_status` field rather than defaulting it. Sign **this** and the genesis packet
carries actual load on day one.

It also exercises the recursion rule usefully: every `evidence_ref` here terminates in a
non-packet type (`file`, `spec`, `adr`, `commit`, `url`), so it is a valid DAG root — the
correct shape for a genesis record with `p: null`.
