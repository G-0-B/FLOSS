# Context Packet — Provenance Chain Integrity, for External Critical Review

**Status:** ⚠️ Specified — this packet asks for review, it does not assert a settled outcome.
**Authored by:** Claude Opus 5 (`claude-opus-5`), Claude Code session, 2026-08-24.
**Operator:** kalisam. **Repository:** `G-0-B/FLOSS`, branch `reconcile/pr38-salvage-20260817` (PR #41).
**Governing decision:** [ADR-20](../adr/ADR-20-provenance-validator-reconciliation.md), D-B3 addendum.

This document is a self-contained brief. A reviewer should not need the originating
conversation. It is written to be *attacked* — the closing section lists the specific
claims I most want falsified.

---

## 1. What the system is

FLOSSI0ULLK runs a Plane A provenance spine: a post-write hook signs a KERI-shaped
packet for every substantive edit and submits a Claim to a local consensus gateway,
which routes it to a multi-model voter panel. Packets form a per-agent hash chain —
each carries `i` (identity), `s` (sequence), `p` (prior packet digest), `d` (SAID),
and `sigs` (Ed25519). Governed `AdrChange`/`SpecChange` claims at System or Substrate
blast radius are refused without valid provenance.

Spec: `docs/specs/provenance-packet.spec.md`. Validator:
`packages/activity_log/provenance.py`.

## 2. What happened

The spine ran from 2026-08-10 and **landed zero claims**. Every hook fired, every
packet was signed, and the validator rejected 100% of submissions. Two causes, both
reproduced and both now fixed (ADR-20 D-A1, D-B3, commit `18d9d9a`).

Then the ancestor-validation question was decided **twice, in opposite directions,
by two agents working the same branch within about an hour**:

| Commit | Behaviour on an unreachable ancestor | Consequence |
|---|---|---|
| pre-`18d9d9a` | Truncate the walk, warn | Deleting a packet made every descendant valid again, silently |
| `18d9d9a` (D-B3) | Scoped artifact checks to depth 0 | Spine worked; ancestor *reachability* left unaddressed |
| `b0de2fe` (parallel agent) | Fatal at every depth | Concealment impossible; spine rejected 100% again same day |
| `61cdd5c` (this work) | Enumerate gaps, refuse bypasses | Both properties held — see §3 |

`b0de2fe` was not wrong on the spec text, which says plainly that "a `p` reference to
a nonexistent prior packet is invalid." It was wrong on a fact neither of us had
stated: **a signed packet cannot be re-derived once lost.** A hole is therefore
permanent, and any rule refusing a chain that contains one refuses that agent forever.

## 3. The rule now implemented

The property worth protecting is not that holes be *impossible*. It is that they be
**undeniable**. Sequence numbers are per-agent and monotonic, so a deleted packet
leaves an arithmetic gap whether or not its file survives.

| Condition | Verdict |
|---|---|
| Expected slot occupied, child points elsewhere | `E_PROVENANCE_CHAIN_FORK` — fatal |
| Expected slot empty | Enumerate exact sequence numbers, resume below, keep verifying |
| Prior further back, skipped slots **empty** | Enumerate — the packets are gone |
| Prior further back, any skipped slot **occupied** | `E_PROVENANCE_SEQUENCE_DISCONTINUOUS` — fatal |
| Chain does not reach sequence 0, or genesis is not sequence 0 | Fatal |

One line: **enumerate what is lost, refuse what is merely bypassed.**

Gaps surface as `E_PROVENANCE_CHAIN_GAP:<n>,<n>` in `warnings`, enumerated rather
than summarised, so an auditor can name exactly which packets to hunt for. Silence
was the defect in the first behaviour; refusal was the defect in the second.

## 4. What running it against live history found

Identity `DkuYPguG98HM2nyR`, 97 packets on disk, sequences 0..100. Three defects,
none introduced by this work, none previously visible:

1. **Four packets absent** — sequences 3, 36, 37, 39. Now enumerated as
   `E_PROVENANCE_CHAIN_GAP:36,37,39` on the head (3 is below a fatal stop).
2. **Sequence 2 points at sequence 0** while sequence 1 is present on disk. A bypass,
   not a loss. Fatal.
3. **Sequence 5 carries `p: null`** — claiming to be genesis at position 5. The chain
   asserts a false origin. Fatal.

Defects 2 and 3 are unrepairable: the packets are signed, so correcting a field
breaks the signature. The proposed remedy is **identity rotation** — start a fresh
chain at sequence 0, retain the existing packets as an audit record with defects
enumerated. Not taken; that is an operator action.

Likely cause is the concurrency defects fixed in the same review sweep (the
`_acquire_lock` stale-reclamation bug, and daemon singleton races), which is
consistent with holes and doubled origins appearing under concurrent writers.

## 5. Adjacent findings a reviewer should weigh

- **Four allow-lists for one vocabulary.** The v1.5 D3 evidence-type widening was
  applied to the spec, the JSON Schema, and `claim_schema.EVIDENCE_TYPES`, but missed
  `_EVIDENCE_REF_TYPES` in `provenance.py` — which was the set actually enforced.
  Second occurrence of this pattern after `spec_gate.GATED_SURFACES`. Fixed by
  binding to one authority; ADR-20 Open Question 4 asks whether a fourth exists.
- **The consent gate is still open.** `entry_has_consent()` accepts any non-empty
  string as `consent_ref.decision_action_hash` without resolving it. Governed claims
  cannot be honestly gated until ADR-12 closes this.
- **The multi-model audit that shaped ADR-20 mislabelled its own agreement.** The
  synthesizer reported "Tier-1, 6/6 unanimous" when one voter answered nothing, one
  dissented on blast radius, and a third question split three ways. Clustering runs
  on whole-response embeddings, so shared formatting outranks opposed conclusions.
  **Any reviewer relying on ensemble output should read `voter_responses[]` directly.**

## 6. Claims I want falsified

Ranked by how much damage a wrong answer does.

1. **"Enumeration makes a hole undeniable."** Is this actually true against a
   motivated adversary? They control the same filesystem. If they delete packet *n*
   AND rewrite the head to claim a lower sequence, does the gap still surface? I
   believe the head's own `s` is signed and so cannot be lowered without breaking the
   signature — but I have not constructed the attack, only reasoned about it.
2. **"Bypassed is distinguishable from lost."** The rule turns on whether a skipped
   slot is occupied *at validation time*. An adversary who bypasses a packet and then
   deletes it converts a fatal into a warning. Is the ordering exploitable?
3. **"Identity rotation is the right remedy for a false origin."** It preserves audit
   but abandons continuity. Is there a repair that keeps the chain, given the packets
   are signed and immutable?
4. **The blast radius of this change.** ADR-20 filed it as System. One audit voter
   argued Substrate (override-forbidden, 0.85) because it relaxes a fail-closed
   governance gate. That dissent is recorded and unresolved.
5. **Whether the spec should change.** This implementation now deliberately departs
   from the literal sentence "a `p` reference to a nonexistent prior packet is
   invalid." Either the spec sentence should gain the lost/bypassed distinction, or
   this implementation is wrong. It should not stay divergent.

## 7. Verification state

- `packages/` + `scripts/tests`: **439 passed**, 1 failed.
- The one failure —
  `test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded`
  — belongs to another agent's in-flight D-B1 audit-view work and fails identically
  at clean HEAD with this work reverted. Confirmed, not assumed.
- `spec_gate --check`: 102 registered, 0 missing, 0 reuse violations, 1 stale.
- ADR-20 registered tier 1 with a reuse block.

## 8. Provenance

| Field | Value |
|---|---|
| Author | Claude Opus 5 (`claude-opus-5`) |
| Date | 2026-08-24 |
| Commits | `18d9d9a` (D-A1 + D-B3), `bad2822` (packet claim-type), `61cdd5c` (chain-gap walk) |
| Branch | `reconcile/pr38-salvage-20260817` → PR #41 |
| Decision record | `docs/adr/ADR-20-provenance-validator-reconciliation.md` |
| Validator | `packages/activity_log/provenance.py` |
| Spec | `docs/specs/provenance-packet.spec.md` |
| Live evidence | `$HOME/.floss_agent/hook.log`; packets under `.agent-surface/provenance/` |
| Prior review | Codex (`chatgpt-codex-connector`) P1s on PR #41, and a 6-voter ensemble audit whose synthesis is at `.agent-surface/reasoning/ensemble/20260824T023542Z_97e6b32c78072e8b_synthesis.json` |

### Signed packet for this document

| Field | Value |
|---|---|
| SAID | `E5tRWQwGSGRFBd9RsgUe1mETatJ1jztkqaVXZYwlhMbU` |
| Sequence | 102 |
| Path | `.agent-surface/provenance/2026-08-24/E5tRWQwGSGRFBd9RsgUe1mETatJ1jztkqaVXZYwlhMbU.json` |
| Artifact refs | this document, ADR-20, `packages/activity_log/provenance.py` (SHA-256 each) |
| Evidence refs | ADR-20, the packet spec, commit `61cdd5c`, the test run, `hook.log` |

Its own validation result, unedited:

```
ok:       False
errors:   ['E_PROVENANCE_SEQUENCE_DISCONTINUOUS']
warnings: ['E_PROVENANCE_CHAIN_GAP:36,37,39']
```

**This packet does not validate, and that is the honest state.** The signature, SAID
and artifact hashes are all sound; what fails is the chain beneath it — the same
history defects catalogued in §4, on an identity that cannot produce a valid governed
claim until it is rotated. A reviewer should treat the artifact hashes as verifiable
and the chain position as compromised. Publishing it any other way would be the exact
failure mode this whole ADR is about.

**Truth-status discipline:** every claim above is ✅ Verified (reproduced against the
working tree) except §4's cause attribution and §6's five items, which are
⚠️ Specified — reasoned, not demonstrated. That is exactly what this review is for.
