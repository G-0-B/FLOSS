# Lane A Probe — the governance authorization anchor, 2026-09-06

**Kind:** evidence record. Plane A. Promotes nothing to canon, changes no code.
**Runs:** the Lane A "first experiment" in
`docs/superpowers/plans/2026-09-05-current-engineering-continuation-packet.md` §5,
against candidate claim C1 in `CCP-EVIDENCE-WORKFLOW-NOW-2026-09-05` §11.
**Truth labels:** ✅ Verified / ⚠️ Specified / 🔮 Aspirational / ❌ Blocked.
Every ✅ carries the command that reproduces it.

---

## 0. Tested state

Recorded because the CCP support conditions require the tested state be named,
and because every finding below is a statement about *this* revision only.

| | |
|---|---|
| Branch | `feat/coordination-room` |
| HEAD | `26fe6ff2623baf4857cd8ee0332e29db7ea76fc9` (2026-09-06 09:48 -0400) |
| Working tree | 35 modified tracked files, none written by this probe |
| Host | Windows 11, Git Bash |
| Toolchain | `cargo` 1.89.0, `rustc` 1.89.0, `wasm32-unknown-unknown` installed |
| Absent | `hc`, `holochain`, `nix` |

---

## 1. The claim under test

```text
C1: A currently executable path exists from a legitimate consent
proposal/decision through the intended substrate to a real committed decision
action whose hash can be consumed by the governed provenance/claim path.
```

## 2. Verdict

**The claim as written cannot be evaluated, because "the intended substrate" is
ambiguous in this repository and the two readings give opposite answers.**

- Read as *the Holochain source chain*, C1 is **inconclusive on this host** and
  **unproven anywhere**: the zome path exists and has tests, but those tests have
  never executed in any environment this probe can verify.
- Read as *the file-based source chain under `packages/source_chain/`*, C1 is
  **already satisfied** — an end-to-end consent path ran on 2026-09-01 and its
  hash sits in a provenance packet today.

This is not the CCP's support / defeat / inconclusive trichotomy. It is a fourth
outcome that framework did not enumerate: **the claim is ambiguous because a term
inside it names two different things.** §7 proposes returning that to the packets.

---

## 3. What was found

### 3.1 A consent anchor now exists in a packet — and it is not a Holochain action ✅ Verified

The received figure in ADR-12, ADR-19 and
`docs/agent-memory/project/adr19-ratification-deferred-to-consent-gate.md` is
"0 of 105 packets carry a `consent_ref`". Both halves have moved:

```
find .agent-surface/provenance -name "*.json" | wc -l          -> 264
grep -rl "consent_ref" .agent-surface/provenance --include=*.json | wc -l  -> 1
```

The one packet is
`.agent-surface/provenance/2026-09-01/EdTWdhoEwrD6uIsqyf6OqZ8LOvnZqk5p_1i0I4YRzZt8.json`,
an `AdrChange` entry from `source_systems: ["hermes", "operator-directive"]`:

```json
"consent_ref": {
  "decision_action_hash": "7bfd8c12942fe9def8aadf1c0ccd79f87f0a263f1a0906d46af791e4cb1eebb0",
  "payload_action_hash":  "a1d1cff537a15d624df34dfcf5735bc5e6fd74cdec94ac3abba9cdd207fc5218"
}
```

Both values are 64-character lowercase hex. A Holochain `ActionHash` is not that
shape. From the vendored upstream source in `docs/research/holochain-holochain.txt`:
Holochain hashes with **Blake2b** to 32 bytes (line 28418), each hash type carries
a 3-byte multihash prefix, and **`ActionHash` renders as `uhCkk…`** in base64url
(line 41974). The only `uhCkk`-shaped strings anywhere in this repository are
inside that vendored corpus and in test fixtures; **no ActionHash this project
produced has ever been recorded here.**

Both hashes resolve — to the *file-based* chain:

```
find ~/.floss_agent/cells -name "7bfd8c12….json"
-> ~/.floss_agent/cells/000…000/source_chain/7bfd8c12….json   type: "consent_decision"
-> ~/.floss_agent/cells/000…000/source_chain/a1d1cff5….json   type: "consent_payload"
```

The decision entry is well-formed and not a placeholder: `outcome: "accepted"`,
`decider_did: "did:operator:anthony"`, a `decision_id` UUID, `scope_granted`, and
a `payload_action_hash` correctly pointing at the payload entry. The payload
carries `blast_radius: "System"`, `consent_scope: ["integrate"]`,
`pattern_id: "workspace-digestion-2026-08-31"`.

So someone built the full shape — proposal → decision → hash → packet — through
the file chain, with a real operator identity. **The structure is faithful. The
substrate is not the one the spec names.** Note also that the cell directory is
`000…000`: a placeholder DNA hash, not a real Holochain DNA.

### 3.2 The anchor's shape is licensed by a false claim in the code ✅ Verified

`packages/source_chain/cell.py:79-92`, in `append_entry`'s docstring:

> "This is the same hash that Holochain uses as the action address, ensuring zero
> rework at migration time."

and its return contract:

> "64-character lowercase hex SHA256 digest (the entry's filename stem)."

The first statement is false. SHA256-hex over canonical JSON is not Blake2b-32
base64url with a `uhCkk` multihash prefix and four location bytes. They differ in
algorithm, encoding, length, and type tagging; they will never coincide.

This matters beyond tidiness. That sentence is the standing justification for
treating a file-chain entry hash as interchangeable with a Holochain action
address — which is exactly what the 2026-09-01 packet does. It is the parent
packet's own boundary violated in a comment: *"Similarity is not identity"* and
*"Serialization is not semantic validation"* (§12).

The same docstring lists the valid entry types as `"genesis", "claim", "vote",
"decision", "memory"`. `consent_payload` and `consent_decision` are not among
them, yet both exist on disk — so `append_entry` does not enforce its own type
list, and nothing in `packages/` writes those two types. The entries were
produced outside this repository's code.

### 3.3 The field has no producer in code ✅ Verified

```
git grep -n "consent_ref" -- '*.py' '*.rs' '*.ts' | grep -v test
```

returns only readers: `provenance.py` (`entry_has_consent`,
`consent_resolution_problems`, `narrative_lines`) and `tools.py:609-613` (the
governed gate). **No code path writes a `consent_ref` into a packet.** The one
packet that has one was hand-assembled.

### 3.4 The gate cannot distinguish the two substrates ✅ Verified

Three layers, none of which constrain the anchor:

| Layer | What it enforces |
|---|---|
| `provenance-packet.spec.md:192` | prose: "points to a source-chain `ConsentDecision` action hash" |
| `provenance-packet.schema.json` | `{"type": "string", "minLength": 1}` — no pattern, no format |
| `entry_has_consent()` | non-empty string, nothing more |

So the spec names a substrate, the schema does not encode it, and the code does
not check it. `consent_resolution_problems()` (added `32577b8`) now emits
`E_CONSENT_GATE_UNRESOLVED` as a warning, which makes the hole visible without
closing it — the right call, and it is doing its job here: the 2026-09-01 packet
would carry that marker today.

### 3.5 The Holochain path exists, is tested, and has never run ✅ Verified

`create_consent_decision` in `ARF/dnas/rose_forest/zomes/consent_coordinator` is
exercised by `ARF/tests/sweettest/tests/consent_zome_test.rs` on
`codex/sweettest-substrate-bridge` (PR #61), which commits through a real
conductor and binds a real `ActionHash` cross-agent, plus a rejected-scope case
proving no decision is created. That is the correct test.

It has not executed anywhere this probe can verify:

- **Not in CI.** The `sweettest` job in `rust-ci.yml` on that branch is gated
  `if: github.event_name == 'workflow_dispatch' || github.event.schedule == '0 5 * * 1'`
  and runs `nix develop path:. --command ./tests/sweettest/run.sh`. Every CI run
  on the branch (2026-08-30, 2026-09-01) was a `pull_request` event, so the job
  was skipped. The one `schedule` run in the last 50 was on `main`, where the
  sweettest crate does not exist.
- **Not on this host.** `cargo test --test consent_zome_test` fails to build:
  `openssl-sys` cannot configure (`Can't locate Locale/Maketext/Simple.pm in
  @INC`). `hc` is absent, and `run.sh` requires both `hc dna pack` and `nix`.
- **The local artifact is from elsewhere.** A 961 MB
  `target/debug/deps/consent_zome_test-80565d9614f7519d` dated 2026-08-31 exists
  in the worktree, but `file` reports **ELF 64-bit LSB pie executable** — built
  under Linux (WSL or a container), unrunnable on this host, and from an
  environment this probe cannot identify or reproduce.

Everything needed is otherwise present: all four release WASMs
(`rose_forest`, `rose_forest_integrity`, `consent`, `consent_integrity`), a
packed `rose_forest.dna`, and the `wasm32-unknown-unknown` target.

A methodological note, because it nearly produced a false result here: the first
run of that test reported `exit code 0` while the build had failed, because the
command was piped to `tail` without `pipefail`. This is the same trap
`.github/workflows/python-ci.yml` documents for its advisory job. **A piped
`cargo test` cannot be used as evidence.**

---

## 4. Answers to the parent packet's Lane A questions

**"Does a functioning source-chain path currently exist that can produce the
required consent decision artifact?"**

Yes, through the file chain, demonstrated once by hand on 2026-09-01. No, through
Holochain, not on any environment with reproducible evidence.

**The falsification condition — "if the repository contains no executable route
from consent decision to a real `decision_action_hash`" — does not fire**, but not
because the route is sound. It does not fire because the gate accepts a route
whose output is not the artifact the spec describes. Reading that as "the anchor
can merely be obtained" would be the error the condition exists to prevent.

**"If running that path requires the missing `hc`/Tryorama substrate: move the
Holochain #28 follow-up into this lane."** On the Holochain reading it does, so by
the parent packet's own rule that follow-up belongs in Lane A. The narrower
blocker is that the sweettest job never triggers on a PR — a `workflow_dispatch`
is one click and would resolve §3.5 without any local toolchain work.

---

## 5. Claim ceiling

What this probe supports:

```text
At 26fe6ff on 2026-09-06, exactly one provenance packet carries a consent_ref;
both of its hashes resolve to file-based source-chain entries and neither is a
Holochain ActionHash; no code writes the field; and no layer of the gate
constrains which substrate the anchor names.
```

What it does **not** establish:

```text
that the Holochain consent path is broken
that the file-chain consent path is illegitimate
that the 2026-09-01 packet was written in bad faith
what decision_action_hash ought to anchor to
that no other environment has run the sweettest successfully
```

The last is a real limit. §3.5 shows the tests did not run in *this repository's*
CI and cannot run on *this* host, and that a Linux binary of unknown provenance
exists. It does not prove nobody ever ran them green somewhere.

---

## 6. Recommendation

**Do not build the bridge yet.** The reason is not caution — it is that
"build the bridge" has two incompatible meanings right now, and choosing one
silently is the ADR-5 violation ADR-19 was deferred to avoid.

Three steps, cheapest first:

1. **Dispatch the sweettest job** (`workflow_dispatch` on
   `codex/sweettest-substrate-bridge`). One click. It converts §3.5 from
   inconclusive to a fact in either direction and needs no local toolchain. It is
   also the adversarial review PR #61 has never had.
2. **Correct `cell.py`'s docstring.** The "same hash Holochain uses" claim is
   false and is load-bearing for the anchor confusion. This is a comment fix with
   no behaviour change, and it removes the standing licence to conflate the two
   substrates. Whether `append_entry` should also enforce its declared type list
   is a separate question.
3. **Then decide what `decision_action_hash` anchors to.** That is ADR-12 design
   work and it is now a genuine fork with a live artifact on each side, not an
   abstraction:
   - *Holochain action* — matches the spec as written; blocked until the
     substrate runs somewhere reproducible; makes the 2026-09-01 packet invalid.
   - *File-chain entry* — already works, already has an operator-signed decision;
     requires amending the spec and admitting the anchor proves consent was
     *recorded locally*, not consented *on a shared substrate*.
   - *Either, explicitly typed* — add a discriminator so a packet says which
     substrate it means, and let `entry_has_consent()` resolve accordingly. Keeps
     the 2026-09-01 work, keeps the Holochain target, costs a schema change.

On the CCP staging question this probe was nominally testing: **Stage 0 held.**
The existing per-iteration engineering contract carried this investigation
without strain — observable outcome, invariants, central uncertainty,
falsification condition and claim ceiling were all expressible in it. Nothing
here demonstrates the promotion condition for a formal `EvidenceContract`.

The one thing the existing contract did *not* express is §2's fourth outcome —
a claim that is neither supported, defeated, nor inconclusive, but **ambiguous
because a term inside it is overloaded**. That belongs back in
`CCP-EVIDENCE-WORKFLOW-NOW` §11 alongside the other three, and it generalises:
the parent packet already warns never to let "anchor" collapse two problems, and
this is the same failure one level down, in "source chain" and "decision".
