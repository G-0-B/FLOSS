---
# --- UpgradableArtifact Header ---
id: "provenance-packet-spec"
version: "1.4.0"
kind: "contract_spec"
status: "Proposed"
updated: "2026-07-30"
supersedes: ["1.3.0", "1.2.0", "1.1.0", "1.0.0"]
truth_status: "specified"   # designed; NOT implemented; NOT validated against repo state
evidence_sources:
  - "FLOSSI0ULLK Master Metaprompt v1.3.1 §8 (Provenance Packet)"
  - "Project Spine v0.5 §5 (Two-Plane), §7 (Provenance Packet)"
  - "RFC 8785 (JSON Canonicalization Scheme)"
  - "KERI/CESR derivation codes — UNVERIFIED against keripy source, see §9"
upgrade_path: "ADR -> pilot 1 week (Claude hooks + gateway) -> promote or revert to warn-only"
rollback_plan: "Revert hard-block to warn-only; keep packet generation active; packets remain valid artifacts"
friction_tier: "high"   # touches identity + consent semantics
license: "Compassion Clause + Apache-2.0"
---

# ProvenancePacketV1 — Cross-Agent Handoff Contract

**Truth status: Specified.** No code implements this yet. Section 9 lists claims that
must be verified against primary sources before code freeze. Do not cite this document
as evidence that the spine exists.

---

## 1. Purpose

A Provenance Packet is a signed, self-addressing, walkable record of a unit of agent
work. It exists so that cross-agent handoffs (Claude, Codex, Gemini, OpenCode,
source-chain Claims, activity logs) carry machine-checkable attribution instead of
arriving as unverifiable prose through the human collision node.

Kernel rule this operationalizes: *no provenance packet -> treat as context, not an
actionable artifact.*

**Non-goals for v1.4:** full KERI (no witnesses, no rotation, no KEL network), remote
verification, revocation, trusted timestamping, multi-human coordination.

---

## 2. Packet Structure

Envelope fields use KERI-shaped names. Payload semantics live in `a[]`.

| Field | Type | Meaning |
|---|---|---|
| `v` | string | Format identifier + serialized byte length (§3) |
| `t` | string | Event type. Fixed: `"prov"` |
| `d` | string | SAID: self-addressing digest of this packet (§4) |
| `i` | string | Agent identifier prefix, derived from Ed25519 verify key (§5) |
| `s` | string | Per-`i` monotonic sequence number, decimal string |
| `p` | string \| null | Prior packet `d` in the **same `i` chain only**; `null` at genesis |
| `a` | array | One or more atomic payload entries (§6) |
| `sigs` | array | Detached Ed25519 signatures (§7) |

### 2.1 `p` versus `evidence_refs` (load-bearing distinction)

- `p` = **intra-agent chain continuity.** Same `i`, previous packet. One chain per `i`.
- `evidence_refs[type="provenance_packet"]` = **cross-agent lineage.** Another agent's
  packet cited as evidence.

Conflating these breaks both the chain invariant and the DAG walk. They are different
relations.

---

## 3. `v` Field

Placeholder during canonicalization: `FLOSSI10JSON000000_`

After the final JCS serialization is produced, replace the final six characters before
the trailing `_` with the lowercase hex byte length of that serialization, zero-padded
to six digits.

Example final value: `FLOSSI10JSON0001a3_`

> **Circularity note.** Length depends on serialization, which contains the length.
> Because the placeholder and the final value are the same byte length, one pass
> suffices: serialize with placeholder, measure, substitute in place. Implementations
> MUST assert that substitution does not change total length.

---

## 4. `d` — SAID Computation Order

Deterministic, ordered, non-negotiable:

1. Construct the packet with all fields populated **except**: set `d` to exactly 44
   `#` characters, set `sigs` to `[]`.
2. Serialize with RFC 8785 JCS over UTF-8.
3. Compute `v` byte length and substitute in place (§3).
4. BLAKE3-256 hash the resulting bytes.
5. Encode as `"E"` + 43-character base64url (unpadded) of the 32-byte digest.
6. Replace the 44-`#` placeholder with the encoded digest.
7. Re-serialize with JCS, `sigs` still `[]`. **These bytes are the signing payload.**
8. Sign (§7), populate `sigs`, re-serialize for storage.

Verification reverses steps 1–7 and checks both the digest and the signature.

---

## 5. `i` — Agent Identifier

`i = "D" + base64url(raw 32-byte Ed25519 verify key)` — 44 characters total.

`B` is reserved for a future non-transferable local-only identifier variant.

### 5.1 Identity layout

```
~/.floss_agent/identity/
  seed          0600  32-byte Ed25519 seed
  verify.key    0644  32-byte raw verify key
  aid           0644  the "D..." identifier string
  seq.json      0600  {"i": "D...", "s": 42, "last_d": "E..."}
```

### 5.2 Sequence and chain state

`s` and `p` are read from `seq.json` under an exclusive advisory file lock
(`fcntl.flock`), incremented, and written via write-temp + `os.replace` atomic rename.

**Fail-closed rule:** if the lock cannot be acquired within 5 seconds, packet creation
FAILS. The calling hook MUST log the failure and MUST NOT silently skip packet
generation. During pilot, hook failure does not block the underlying edit — it emits a
warning and an audit-visible gap record.

### 5.3 Key loss

There is no rotation in v1.4. If the seed is lost or compromised: generate a new `i`,
start a new chain at `s=0`, `p=null`, and cite the last packet of the dead chain via
`evidence_refs[type="provenance_packet"]`. Record the transition in canon. This is a
documented degradation, not a recovery.

---

## 6. `a[]` — Payload Entries

Each entry is atomic and independently validated. A packet may bundle several.

```
{
  "claim_type":        "observed_fact" | "repo_assumption" | "proposal" | "target"
                       | "consent_grant",
  "truth_status":      "verified" | "specified" | "aspirational" | "unverified",
  "created_at":        ISO8601 UTC, self-asserted (see §9.4)
  "source_systems":    [string, ...],
  "human_collision_node": string | null,
  "action_ref":        string | null,          // activity_log Action id
  "consent_ref":       string | null,          // ConsentDecision action hash
  "consent_payload_ref": string | null,        // optional parent ConsentPayload hash
  "artifact_refs":     [{ "path": string, "sha256": string }, ...],
  "evidence_refs":     [{ "type": ..., "ref": string, "sha256": string|null }, ...],
  "summary":           string,   // <= 15 lines
  "risks":             [string, ...],
  "benefits":          [string, ...],
  "next_action":       string,
  // reserved, unset in v1.4:
  "keri_event_ref":       null,
  "a2a_entity_card_ref":  null,
  "in_toto_predicate_type": null,
  "prov_o_activity_id":   null
}
```

### 6.1 Evidence types

`spec` · `test` · `adr` · `url` · `commit` · `file` · `log` · `activity` ·
`source_chain` · `provenance_packet`

### 6.2 Recursion rules

- Evidence graph is a **DAG**, not a tree.
- Max packet-reference depth: **8**.
- Cycles: invalid.
- Nonexistent referenced packet: invalid.
- Every chain MUST terminate in non-packet evidence: `adr`, `commit`, `test`, `file`,
  `source_chain`, or `url`.

---

## 7. `sigs`

Detached Ed25519 signature over the §4 step-7 bytes, encoded as `"0B"` +
base64url(raw 64-byte signature).

Signing key is the seed at `~/.floss_agent/identity/seed`, via PyNaCl `SigningKey`.

> **Threat-model honesty.** In the pilot topology the signing key and the signed
> artifacts live under the same uid on the same machine. Any process that can write
> the artifacts can also read the key and sign. Ed25519 here buys *shape* — future
> rotation, future remote verification, future KERI migration — not present-day
> resistance to a local attacker. Do not describe v1.4 as providing non-repudiation.

---

## 8. Enforcement

### 8.1 Hybrid mode

| Case | Behavior |
|---|---|
| Ordinary edit, packet missing | Warn + audit record |
| Ordinary edit, packet invalid | Warn + audit record (error severity) |
| Governed `System`/`Substrate` binding without valid packet **and** `consent_ref` | **Hard-block** at gateway |

Governed patterns: `kernel`, `constitution`, `adr`, `skill`, `voter_persona`,
`frame_translation`, `consent_policy`.

### 8.2 Bootstrap exemption (REQUIRED — see §10.1)

The hard-block depends on `ConsentDecision` action hashes from the Rose Forest consent
coordinator. If that substrate is not running, the hard-block cannot be satisfied and
would lock out all governed edits — including edits to this spec.

Therefore: implementations MUST support a `PROVENANCE_BOOTSTRAP=1` environment
exemption that downgrades the hard-block to warn-only, MUST emit a loud audit record
whenever the exemption is active, and MUST NOT enable it by default. Removal of the
exemption is a v1.5 gate, not a v1.4 requirement.

### 8.3 Plane B re-validation

When a Claim cites `type="provenance_packet"`, `GatewayTools.submit_claim()` MUST:
re-read the packet from disk, re-canonicalize, recompute the SAID, verify the
signature, verify every `artifact_refs[].sha256` against current file content, and walk
the evidence DAG per §6.2 — **before** accepting the Claim. Plane B never trusts
cached packet metadata. (Project Spine v0.5 §5 bridge rule.)

Artifact-hash mismatch is expected when files change after packet creation. Mismatch
MUST be reported as `stale`, distinguished from `tampered`, and MUST NOT be silently
accepted.

---

## 9. Claims Requiring Primary-Source Verification Before Code Freeze

Marked **Unverified**. A CESR derivation-code error was already made and corrected once
during this design (`B` incorrectly described as transferable). Treat the rest with
matching suspicion.

| # | Claim | Verify against |
|---|---|---|
| 9.1 | `D` is the correct CESR code for a transferable-context Ed25519 verify key, and `B` for non-transferable | `keri/core/coring.py` derivation-code tables |
| 9.2 | `E` is the BLAKE3-256 digest code and yields 43 base64url chars + 1 code char = 44 | keripy Matter/Diger code tables |
| 9.3 | 44 `#` characters is the correct SAID placeholder width for a 44-char `d` | keripy `saider` / SAID algorithm |
| 9.4 | `0B` is the correct code for a 64-byte Ed25519 signature (2-char code + 86 base64url = 88) | keripy Indexer/Siger tables |
| 9.5 | A `t` value outside KERI's registered event types will not break future keripy parsing | KERI spec event-type registry |
| 9.6 | "Later KERI migration is additive" — **currently Aspirational.** Real KERI inception requires `kt`, `k`, `n`, `bt`, `b`, `c`, `a` with defined semantics; a `prov` event type does not exist in KERI | KERI spec §inception/interaction events |
| 9.7 | A maintained RFC 8785 JCS package exists for Python and produces byte-identical output to the spec's test vectors | PyPI + RFC 8785 test vectors |
| 9.8 | `blake3` Python package provides BLAKE3-256 with stable output | package docs |

**If 9.6 fails** — i.e. migration is not additive — the KERI-shaping still buys
readable field conventions and a stable schema, but the "collapses two future
migrations into one" rationale is void and should be struck from the ADR.

---

## 10. Pilot

- **Scope:** Claude hooks + consensus gateway. One agent surface. One week.
- **Other agents:** Gemini, Codex, OpenCode audit-visible, not enforced.
- **Daily check:** `python FLOSS/scripts/audit_provenance_packets.py --since 24h`
- **Success signal:** at least one of — a real audit catch, a shadow hard-block that
  would have prevented a governed binding, a rollback assisted by packet lineage, or a
  prevented overclaim.
- **Rollback:** if no success signal after one week, revert hard-block to warn-only,
  keep packet generation active, revise before broader rollout.

### 10.1 Known pilot design weakness

The pilot scope is one agent surface, but the NOW pain is *cross-agent* handoff drift.
A single-surface pilot tests plumbing, not the value proposition. A null result is
therefore ambiguous: it may mean the design is wrong, or it may mean the test could not
observe the phenomenon. Before drawing conclusions from a null result, consider a
second-week scope extension that routes one real Codex handoff through the manual
`floss prov pack` path.

---

## 11. Test Order

1. **Genesis test (gate).** Encode the v1.4 plan handoff as a packet; verify it
   validates. Nothing else ships if this fails.
2. JCS byte stability against RFC 8785 test vectors.
3. `v` length substitution preserves total length.
4. SAID placeholder order; digest stability across runs and processes.
5. `i` derivation; `0B` signature verify; forged signature rejected.
6. Sequence lock under concurrent writers; atomic replace; lock-timeout fails closed.
7. Nonexistent `p` rejected; cycle rejected; depth-9 rejected; non-packet root required.
8. Gateway: stale artifact hash reported as stale; tampered reported as tampered;
   invalid signature rejected; governed binding without `consent_ref` blocked;
   bootstrap exemption downgrades and logs.
9. Multi-entry narrative projection: one line per `a[]` entry, shared packet id.
10. Focused suite + shared-surface materializer `--check`.

---

## 12. Narrative Projection

One line per `a[]` entry:

```
[2026-07-30T14:22Z] D4kf..q2 ◇ proposal -> activity_log/provenance.py · evidence: 3 refs · governed: no · sig: ok
```

Multi-entry packets emit multiple lines sharing the packet `d`.

---

## 13. Deferred (LATER / not in v1.4)

Revocation and supersession of signed packets (§ open problem — a signature proves who
said it, not that it is true; v1.4 has no way to update a signed `truth_status`) ·
key rotation and pre-rotation · witnesses and KEL publication · trusted timestamping ·
remote verification · Merkle rolling-summary packets for write amplification ·
`agentmemory` stale-recall invalidation · multi-session `i` coordination policy ·
A2A / in-toto / PROV-O bridges.
