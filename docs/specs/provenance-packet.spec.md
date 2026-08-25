# Provenance Packet Spec v1.4 (+ v1.5 edits D2, D3)

Applied 2026-08-10 from `docs/research/intake_raw/2026-08-10-root/reports/provenance-packet-v1.5-delta.md`:

- **D2 — multisig headroom.** `sigs` no longer pins `maxItems: 1`. Exactly one
  signature is still required today; the array form is retained so threshold
  signing (KERI `kt`/`k`) becomes additive rather than a breaking schema change.
- **D3 — evidence-type extension.** `file`, `log`, `activity`, `source_chain`
  added to the evidence-root vocabulary, in this spec, in
  `provenance-packet.schema.json`, and in `EVIDENCE_TYPES` in
  `packages/orchestrator/claim_schema.py`.

**D1 (bootstrap exemption) is deliberately NOT applied** — it is blocked on
ADR-12 per `CONTEXT.yaml.consent_gate_defect.do_not`. D4–D6 remain unapplied
proposals in the delta document.

The delta is an edit-set against this spec, not a replacement: this file stays
authoritative. Corrections edit the original; parallel specs are the failure
mode that produced a 25 KB adversarial review orbiting a 20 KB artifact,
forever unmerged.

Status: Specified for Plane A pilot. This spec defines the packet contract used by
local agent surfaces and the consensus gateway before any Plane B/Holochain
source-chain ingestion. It is KERI-shaped but not full KERI: witnesses, key
rotation, and KEL publication are deferred.

## Purpose

The provenance packet is the machine-verifiable handoff unit for cross-model and
cross-agent work. A load-bearing artifact without a valid packet may still be
read as context, but governed System/Substrate pattern bindings are blocked
until they carry valid provenance and an explicit consent reference.

Observed NOW pain: status and adoption claims have drifted across REST checks,
MCP checks, activity-log rows, and human-pasted cross-agent handoffs. This packet
spine makes those handoffs signed, walkable, and auditable.

## Envelope

Packets are JSON objects canonicalized with RFC 8785 JCS over UTF-8 bytes.

Required top-level fields:

| Field | Type | Rule |
|---|---|---|
| `v` | string | `FLOSSI10JSON000000_` shape; final six hex chars encode final JCS byte length. |
| `t` | string | Literal `prov`. |
| `d` | string | Self-addressing digest: `E` + 43-char base64url BLAKE3-256 digest. |
| `i` | string | `D` or `B` + 43-char base64url Ed25519 verify key; `D` is transferable and `B` is non-transferable, and both are valid signing identifiers in v1.4. |
| `s` | string | Gapless per-`i` sequence, decimal string: genesis is `0`; every successor equals the latest sequence for the same `i` plus one. |
| `p` | string or null | Prior packet digest in the same per-`i` chain only. |
| `a` | array | One or more payload entries. |
| `sigs` | array | Ed25519 signatures: `0B` + 86-char base64url raw signature each. v1.5 requires exactly one; the array form is retained so threshold signing is additive. |

`p` is only intra-agent chain continuity. Cross-agent lineage uses
`a[].evidence_refs[type=provenance_packet]`, not `p`.

## Payload Entry

Each `a[]` entry is an atomic claim payload. Multi-entry packets are allowed for
bundled handoffs, but validation and governed enforcement happen per entry.

Required payload fields:

| Field | Type | Rule |
|---|---|---|
| `claim_type` | string | Local claim/action class, such as `proposal`, `CodeChange`, `SpecChange`. |
| `truth_status` | string | Project truth label, usually `specified` until independently verified. |
| `source_systems` | array | Agent/model/tool surfaces that contributed to the payload. Payload-level, not envelope-level. |
| `created_at` | string | UTC ISO 8601 timestamp. |
| `human_collision_node` | string | Human or operator node that bridged the handoff when applicable. |
| `artifact_refs` | array | Content-addressed artifacts; each item has `path` and `sha256`. |
| `evidence_refs` | array | Evidence roots; at least one non-packet evidence root is required across the DAG. Types: `spec`, `test`, `adr`, `url`, `commit`, `provenance_packet`, `file`, `log`, `activity`, `source_chain`. |
| `risks` | array | Known risks or empty list. |
| `benefits` | array | Known benefits or empty list. |
| `next_action` | string | Immediate next action or disposition. |

Optional compatibility fields live inside `a[]`, not the envelope:

- `consent_ref`: object with `decision_action_hash` and optional `payload_action_hash`.
- `keri_event_ref`
- `a2a_entity_card_ref`
- `in_toto_predicate_type`
- `prov_o_activity_id`

## SAID And Signature Algorithm

1. Build packet with `v = "FLOSSI10JSON000000_"`, `d = "#" * 44`, and `sigs = []`.
2. Canonicalize with RFC 8785 JCS and compute BLAKE3-256.
3. Set `d = "E" + base64url_no_padding(digest)`.
4. Set `sigs = ["0B" + "A" * 86]`, canonicalize, and set `v` to
   `FLOSSI10JSON{len(final_bytes):06x}_`.
5. Reset `sigs = []`, reset `d = "#" * 44`, canonicalize, recompute BLAKE3-256,
   and set final `d`.
6. Sign canonical bytes with final `v`, final `d`, and `sigs = []`.
7. Set `sigs = ["0B" + base64url_no_padding(raw_ed25519_signature)]`.

Validation MUST verify signature over canonical bytes with `sigs = []`, recompute
`d`, check the `v` byte length against final canonical packet bytes, and re-hash
all artifact refs.

## Recursion Semantics

Evidence references form a DAG, not a tree. Validation rules:

- Max recursion depth is 8.
- Cycles are invalid.
- A packet whose evidence DAG contains no non-packet evidence root is invalid.
- `p` is a linear per-agent sequence pointer. It is checked for existence and
  continuity but does not consume the evidence-DAG recursion budget.

### Missing Priors — Lost Versus Bypassed

Amended 2026-08-25 per ADR-20's D-B3 addendum, after a four-audit external review.
The previous sentence — "a `p` reference to a nonexistent prior packet is invalid"
— is **superseded**. It was unqualified, and enforcing it literally rejected 100%
of submissions from any agent whose chain had ever lost a packet. A signed packet
cannot be re-derived, so a hole is permanent: a rule refusing chains that contain
one refuses that agent forever.

Sequence numbers are per-agent and monotonic, so a deleted packet leaves an
arithmetic gap whether or not its file survives. Validation resolves each break
against the per-identity sequence index:

| Condition | Verdict |
|---|---|
| Expected slot holds a **valid signed** packet the child does not point at | `E_PROVENANCE_CHAIN_FORK` — invalid |
| Expected slot empty | `E_PROVENANCE_CHAIN_GAP:<n>` warning, enumerated by sequence number; the walk resumes below the gap and continues verifying |
| Prior exists further back, skipped slots **empty** | Enumerated as a gap |
| Prior exists further back, any skipped slot **occupied** | `E_PROVENANCE_SEQUENCE_DISCONTINUOUS` — invalid |
| Chain does not reach sequence 0, or genesis is not sequence 0 | Invalid |

The rule: **enumerate what is lost, refuse what is merely bypassed.** Only a valid
signature establishes that a slot is occupied; unsigned or malformed JSON naming a
position does not.

### Known Limits Of Gap Enumeration

Stated here because an unstated limit reads as a guarantee. Both were confirmed by
independent external audit (2026-08-25) and neither is closed by this contract.

1. **Wholesale head truncation is not detected.** Enumeration finds gaps relative
   to the highest sequence number still present. An adversary with write access to
   the packet store can delete everything above sequence *n* and present *n* as
   current; nothing inside a self-signed chain distinguishes that from an agent
   that has simply not written since *n*. Detection requires an **external anchor**
   — a periodically published, externally observed commitment to the chain head.
   Until one exists, this spec's integrity claims hold only against a
   buggy-but-honest writer, not against control of the store.

2. **Bypass-then-delete downgrades a refusal to a warning.** The fatal/enumerated
   distinction is evaluated against occupancy *at validation time*. An adversary
   who first points past a live packet and later deletes it converts
   `E_PROVENANCE_SEQUENCE_DISCONTINUOUS` into `E_PROVENANCE_CHAIN_GAP`. Closing
   this needs a second, append-only record of occupancy that deletion cannot reach.

Both limits are the same missing primitive: nothing outside the packet store
witnesses what the store contained. See ADR-20's trust boundary section.
- Plane B MUST re-run all packet validation steps; it never trusts a cached packet
  digest or a caller-provided hash.

## Audit Disposition

Strict packet validation and operator-facing daily audit are separate views.
`validate_packet()` remains strict: if an artifact ref no longer hashes to the
packet's recorded `sha256`, the packet is not valid current evidence.

Daily Plane A audit MAY classify a strict
`E_PROVENANCE_ARTIFACT_HASH_MISMATCH` as `superseded` instead of active
`invalid` when the packet is historical evidence for mutable generated outputs
or when a newer valid packet from the same agent covers the same claim/artifact
surface. Superseded packets are preserved and reported, but they do not satisfy
governed-claim evidence requirements and must not be treated as current truth.

The operator-facing audit statuses are:

| Status | Meaning |
|---|---|
| `valid` | Strict packet validation passes against the current workspace. |
| `superseded` | Signature/digest structure is preserved, but artifact refs point at old generated or replaced workspace content covered by later evidence. |
| `invalid` | The packet has an active validation failure that is not covered by the supersession policy. |

## Governed Boundary

Hybrid enforcement applies:

- Missing packets for ordinary Plane A activity are warning/audit events.
- A System/Substrate `AdrChange`, `SpecChange`, or `ConfigChange` claim is blocked
  unless it has a valid `provenance_packet` evidence ref and at least one payload
  entry has `consent_ref.decision_action_hash`.

`consent_ref.decision_action_hash` points to a source-chain `ConsentDecision`
action hash. `consent_ref.payload_action_hash` may point to the parent
`ConsentPayload`.

Conflict precedence is:

1. Repository canon.
2. Source-chain `ConsentDecision`.
3. Verified provenance packets and activity-log rows.
4. `agentmemory` recall.

`agentmemory` never participates in packet verification.

## Pilot

Pilot scope is Claude hooks plus the consensus gateway for one week. Daily audit
reports emit one narrative line per payload entry.

Rollback trigger: if the pilot produces no evidence-positive event after one
week, hard-blocking reverts to warn-only, packet generation stays enabled, and
broader propagation waits for the next iteration.

Success marker: the first real cross-agent handoff that validates through this
spine. Suggested genesis note:

> Genesis: [timestamp]. Agent [i] handed off [claim_type] to [recipient agent]
> via packet d=[digest]. Validated, walked, and consumed. Provenance Spine is
> load-bearing from this moment.
