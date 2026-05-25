# Provenance Packet Spec v1.4

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
| `i` | string | Agent identifier: `D` + 43-char base64url Ed25519 verify key. `B` is reserved for non-transferable identifiers. |
| `s` | string | Monotonic per-`i` sequence, decimal string. |
| `p` | string or null | Prior packet digest in the same per-`i` chain only. |
| `a` | array | One or more payload entries. |
| `sigs` | array | One Ed25519 signature: `0B` + 86-char base64url raw signature. |

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
| `evidence_refs` | array | Evidence roots; at least one non-packet evidence root is required across the DAG. |
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
- A `p` reference to a nonexistent prior packet is invalid.
- Plane B MUST re-run all packet validation steps; it never trusts a cached packet
  digest or a caller-provided hash.

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
