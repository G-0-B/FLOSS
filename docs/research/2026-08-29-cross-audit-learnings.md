# Cross-audit learnings — the anchor review and the materializer audit

Date: 2026-08-29
Sources:
- `.toilet/2026-08-25-mulit-model-family-senior-architect-audit_ADR_18_MATERIALIZER_REUSE_PLAN_v2-1.md`
- `.toilet/tinycortex_OPENHUMAN_MEMORY.md`
- `docs/reviews/2026-08-29-model-identity-anomoly/` (the anchor review)

## Are the audits any good?

**The materializer audit: yes, and it is the best-shaped audit this project has
received.** Four properties worth copying:

1. **It challenges the plan's own authority.** *"The plan's §2 audit synthesis
   table cites Grok 4.6, Claude Sonnet 5, and Kimi K3 … No session transcript,
   cryptographic session hash, or durable artifact supports this attribution.
   Under in-toto framing, this would be an unsigned attestation by an unknown
   key."* Auditing the evidentiary standing of the thing being audited is rare
   and is the single most useful move in the document.
2. **It separates reinvention from genuine novelty** rather than declaring
   everything reinvented. It names the signed-gradient consensus gateway and the
   D7 spec-gate as correctly bespoke.
3. **Risks carry severity and a mechanism**, not adjectives.
4. **It supersedes itself explicitly** — the third pass says "the complete prior
   audit stands" and adds only differentials.

Two things it gets wrong or leaves soft, on spot-check:

- **It recommends shelling out to `cosign`.** `sigstore` is on PyPI at 4.5.0 as a
  pure-Python client. Recommending a Go binary subprocess when a library exists
  is the same error the OpenTimestamps probe found: the CLI is the fragile part
  (`ots` is entirely unusable on this platform; the library API works fine).
  Verified: `in-toto` 3.1.0, `in-toto-attestation` 0.9.3, `sigstore` 4.5.0 all
  exist and are current.
- **Supply-chain version claims are cited but unprobed.** `allagents v1.13.4`
  and the corrected repo paths are asserted against public sources; none was
  installed or run. By this project's own ADR-18 standard that is a *search*, not
  a probe.

**TinyCortex: interesting, honest about its own weakness, not currently
actionable.** It is a draft describing a memory architecture — retention-weighted
decay, a background consolidation loop, conscious/subconscious separation. Its
own Evaluation section says the evidence is "primarily qualitative" with
benchmarking "in progress", which is the right disclosure and also the reason not
to build on it yet. One idea is worth keeping regardless of the paper's fate:
**retention should be a function of access frequency, recency and utility, with
periodic pruning** — which is a sharper statement of the doc-budget rule this
project already has, and applies directly to `docs/agent-memory/`. Nothing here
justifies a new subsystem.

## The finding that matters: the same defect, four times

The materializer audit and the anchor review were conducted independently, by
different panels, against different artifacts. They found the same defect class:

| | Commitment layer | Witness / attestation layer |
|---|---|---|
| Provenance anchor | Merkle set commitment — sound | Git tag: half broken, never exercised |
| Provenance packets | BLAKE3 + Ed25519 — sound | KERI-*shaped*, not KERI-compatible (spec §9) |
| Materializer | BLAKE3 hashline — sound | No signed attestation; SLSA L1 equivalent |
| Review records | Real reviews, 9 reviewers | Unresolvable path, then unpinned content |

**This project reliably builds the commitment and improvises the witness.** The
hard cryptographic part is done carefully every time; the part that makes it
legible to an outsider is invented on the spot every time. That is not four
coincidences, it is a systematic bias — and it is legible from the outside, which
is why two unrelated panels both found it.

The corollary is a design rule: **the witness is the part to adopt.** A
commitment must be built to fit the data; a witness must be recognisable to
someone who does not trust you, which is exactly what a standard is for.

## Acted on immediately

**The reuse gate could not detect a swapped review record.** `_record_problems`
checked path shape, containment, existence and regular-file — never content. So
a record could be replaced wholesale after the gate passed and the gate would
keep passing. That is the audit's "unsigned attestation by an unknown key", found
in our own gate rather than in a plan.

`reuse.reviewer.record_sha256` now pins it. Optional and fail-open: entries
without a pin are unaffected, because tightening a validator against existing
history without enumerating what breaks is CF-1. The digest is **line-ending
normalised**, or it would verify only on the machine that wrote it — CF-8 one
layer down. Verified to fail closed on a one-line edit to the pinned record.

## Backlog, ordered by what the evidence supports

### Now — small, confirmed, mine

- **Confirm the OpenTimestamps witness.** Run `witness-upgrade` once Bitcoin
  confirms. Until then the external-witness claim is ⚠️ Specified, not ✅.
- **Pin the remaining review record** (`2026-08-24-adr20-adversarial-audit`) the
  same way.
- **`G10` — the anchor scan is still not atomic.** Publish now writes through a
  temp file, but `scan_packets` has no lock. `provenance.py:151-233` already has a
  lock that handles Windows `DELETE_PENDING` and stale reclamation, written in
  response to an observed flake. **Reuse it rather than writing a third one** —
  and the materializer's `sync-state.json`, which the audit flags for the same
  defect, should use it too. One lock, three call sites.

### Next — the standards adoption both audits point at

- **Wrap provenance packets in an in-toto Statement.** `in-toto` 3.1.0 and
  `in-toto-attestation` 0.9.3 are on PyPI. This is the packet-layer version of
  what OpenTimestamps did for the anchor layer: keep the commitment, adopt the
  envelope. It also retires spec §9's awkward position — packets stop being
  KERI-shaped-but-incompatible and become a format with an actual reader.
- **Sigstore for signing, via the Python client, not `cosign`.** Fulcio's
  OIDC-bound short-lived certificates are the real answer to "who signed this
  audit", which is currently a prose citation.
- **Then reconsider Rekor.** With in-toto envelopes in place the marginal cost
  drops a lot, and the anchor review's `G2` (6 reviewers) wanted it.

### Open, unresolved, and not mine to decide

- **`G12` — republishing a consistent anchor over a truncated store still
  returns VERIFIED.** OpenTimestamps improves it (the earlier proof cannot be
  deleted) without closing it.
- **`GROK/F11` — "should not ship in this form"** is still formally unrefuted.
  My reading: right about the form it was in, wrong as a verdict on the whole —
  the set commitment is sound and irreducible; the witness was built when it
  should have been composed, and now is composed.
- **`CF-9` — a green gate does not mean an approved review.** Proposal recorded,
  deliberately not implemented.
- **The contested RFC 6962 cluster** (`GEM31/F6` vs `META/F4` vs `GROK/F9`) —
  three reviewers, incompatible conclusions about the cryptographic core, nobody
  has adjudicated.
- **Identity rotation** for the damaged live chain — operator action, outstanding
  since before this session.

### Cross-implementable from the materializer audit specifically

- **A conformance probe for "enforcing" harnesses.** The audit's Risk 1 is that
  Tier A clients are *assumed* to honour blocking `PreToolUse`, with no runtime
  test. This is the same shape as the anchor's tag carrier being assumed to work
  and never exercised (`GROK/F3`), and as the ADR-20 record being assumed to
  resolve. **Rule worth generalising: any mechanism whose value depends on it
  actually firing needs a test that it fires — separate from a test that it is
  configured.**
- **Checkpoints should be hashed into the provenance ledger.** The recovery
  anchor is currently unsigned, which is `G1` in a different file.
- **Dual-hash with SHA-256 where a regulated reader might appear.** Partially
  true already: the OpenTimestamps digest is SHA-256 over the root, so the anchor
  now has a FIPS-friendly path by accident. Worth making deliberate.
