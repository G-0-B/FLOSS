# Merge groups — draft for operator adjudication

**Status:** DRAFT. Nothing here is decided.
**Input:** 68 findings across 10 reviewer files (9 distinct reviewers — see G-DUP).
**Output:** `merge.json`, consumed by `scripts/review_independence.py --merge`.

## Conflict of interest, stated up front

**I wrote the artifact these reviews attack.** Grouping findings is a judgment
call, and an author has an obvious incentive to merge aggressively — collapsing
five distinct problems into one "already known" bucket makes a review look
survivable. Three mitigations, all checkable:

1. **Severity is never a merge criterion.** Groups are formed on defect identity
   only. `G4` merges a `critical` with a `minor` because they name the same bug.
2. **Contested findings are deliberately NOT merged.** Where reviewers disagree
   with each other, merging would manufacture agreement. See *Contested* below.
3. **Every finding is accounted for.** 68 in, 68 assigned, 0 dropped. The
   generator asserts this and refuses to emit on a double-assignment.

Reject any group you disagree with; the map is a plain dict keyed by
`location::claim`.

## Effect of merging

| | Raw | Merged |
|---|---|---|
| Distinct findings | 62 | **31** |
| Raised by >1 reviewer | 6 (10%) | **12 (39%)** |
| Mean pairwise φ | −0.096 | **+0.096** |
| n_eff (Kish) | *refused* | **5.36** (k=10) / **6.66** (k=9) |
| n_eff (eigenvalue) | — | 3.38 / 4.12 |
| Independence ratio | — | 53.6% / **74.0%** |

k=9 collapses the duplicate pair. **That is the honest k.**

For comparison, arXiv:2605.29800 measured n_eff ≈ 2.18 for 9 frontier judges
across 7 families **without tools**. This panel, with retrieval, measures 6.66 on
the Kish estimator. Consistent with the tool-access hypothesis and **not yet
evidence for it** — different task, different item construction (findings-raised,
not errors-against-gold), and a grouping authored by the artifact's author.
The eigenvalue estimate (4.12) is lower and the two disagreeing is itself a
caution: the paper's estimators agreed to within 0.02 on its corpus.

## High-consensus groups

### G1 — `signer` is excluded from the signed bytes (5 findings, 4 reviewers)
`ANTI/F2` `DEEP/F1` `UNSURE/F1` `META/F5` `PXGROK/F2`

The signature does not bind the claimed signer identity, so any valid signature
can be re-attributed to another `signer` value. ANTI names it DSKS
(duplicate-signature key selection). **Real** — `anchor_signing_bytes` strips
both `sig` and `signer`, and the spec documents that as intentional. Documenting
a hole does not close it.

### G2 — ADR-18 ladder: an existing external log should have been adopted (7 findings, 6 reviewers)
`DEEP/F3` `UNSURE/F3` `GROK/F5` `META/F7` `PXGEM/F7` `PXGROK/F4` `GLM/F3`

Rekor, SCITT, Trillian, and — named by three reviewers and **absent from the
survey entirely** — OpenTimestamps. `PXGEM/F7` puts it most sharply: the
no-network-egress justification is a preference misframed as a principled
constraint. **The strongest consensus in the corpus, and it is against the
central design decision.**

### G6 — the git tag / event firehose is not an immutable external witness (7 findings, 6 reviewers)
`ANTI/F3` `DEEP/F2` `UNSURE/F2` `GEM31/F5` `GROK/F4` `META/F3` `PXGEM/F6`

Tags are mutable and force-pushable; mirrors need not retain historical tag
values; the firehose records refs and messages, not the packet set; GH Archive
needs a paid BigQuery query to consult. This attacks the one mechanism the spec
called "the one place a fact outside the operator's control is created."

### G4 — `ANCHOR_STALE` is a count comparison, not a subset check (5 findings, 4 reviewers)
`DEEP/F6` `UNSURE/F6` `GLM/F2` `GROK/F1` `PXGEM/F1`

**CONFIRMED BY REPRODUCTION.** Deleted an interior packet, added two unrelated
ones, re-verified:

```
after interior deletion + net growth: ANCHOR_STALE
  packet_delta: 1   vanished: []   head_regressions: []
```

`anchor.py` reads `elif len(leaves) > packet_count` while the comment beside it
claims "nothing anchored has gone". Nothing checks that. **A deleted packet is
reported as honest growth.**

### G5 — the `prev_root` walk is specified and unimplemented (4 findings, 4 reviewers)
`GLM/F4` `GROK/F2` `PXGEM/F2` `PXGROK/F1`

**CONFIRMED.** `prev_root` is only ever written; `grep` finds no read in
`verify_anchor`. Worse, as `GROK/F2` notes, `publish` writes a single
`anchor.json` and overwrites it — so there is no series to walk even if the walk
existed. The spec's Verify step 2 describes a capability that does not exist.

### G10 — scan and write are not atomic (5 findings, 4 reviewers)
`DEEP/F4` `UNSURE/F4` `META/F6` `PXGEM/F9` `PXGROK/F5`

No lock, no snapshot; `write_bytes` is non-atomic; a partial write that is still
valid JSON becomes a real leaf.

### G12 — republishing over a truncated store returns VERIFIED (3 findings, 2 reviewers)
`DEEP/F5` `UNSURE/F5` `GROK/F8`

`GROK/F8` states it as a direct contradiction of the spec's own one-line scope:
"silent wholesale truncation impossible" is false once the operator publishes a
fresh consistent anchor over the truncated store. **This is the artifact's
headline claim, contradicted.**

## Smaller groups

| Group | Findings | Reviewers | Claim |
|---|---|---|---|
| `G3` git is already a Merkle tree | `ANTI/F4` `GEM31/F1` | 2 | Custom tree is redundant with git's own |
| `G9` key auto-mint, pinning off by default | `GROK/F7` `PXGEM/F3` | 2 | `load_or_create_identity` silently mints; `--expect-signer` defaults None |
| `G11` `unreadable[]` can mask truncation | `GEM31/F4` `PXGEM/F4` | 2 | Lock a file instead of deleting it; verify never diffs the list |
| `G13` misc threat-model omissions | `GROK/F10` `META/F8` `PXGROK/F7` | 3 | Different specific omissions, kept together as a class |
| `G22` tier-2 review not performed | `META/F1` `PXGROK/F8` | 2 | Already self-declared in the spec's Outstanding section |
| `G8` artifact not retrievable | `PXTERRA/F1..F3` | 1 | Could not fetch the branch; **a retrieval failure, not a defect finding** |

Singletons, one reviewer each: `G6b` PushEvent no longer carries commit messages
(GLM, **a specific factual claim that would kill G6's mechanism — verify first**),
`G7` no tags exist and the CLI never creates them, `G14` sorting breaks
consistency proofs, `G16` unbounded `max_seq` memory bomb, `G17` JCS duplicate
keys, `G18` git would reject the tag name (**likely wrong** — ambiguity rules
apply to 40-hex names), `G19` `--max-output` truncates JSON, `G20` version field
unchecked, `G21` Events API retention cut to 30 days, `G23` "inclusion proof"
language implies proofs that do not exist, `G24` no liveness alarm on perpetual
STALE, `G25` misleading test name (**correct — the test asserts the opposite of
its name**), `G26` no-egress claim contradicted by git push, `G27` moved-packet
test is weaker than the spec claims, `GS` should not ship in this form.

## Contested — deliberately NOT merged

`GEM31/F6` `META/F4` `GROK/F9`

Three reviewers on the same subject reaching incompatible conclusions:

- `GEM31/F6` — odd-node promotion **violates** RFC 6962.
- `META/F4` — domain separation and odd-node promotion **follow** RFC 6962 best
  practice and block CVE-2012-2459.
- `GROK/F9` — the construction is **not the exploitable part**; no
  second-preimage or ambiguous packet-set found.

Merging these would record agreement where there is a live disagreement about
the cryptographic core. They stay separate. **Someone here is wrong and it
matters.**

## G-DUP — two files, one reviewer

`deepseek-web-no-tools` and `unsure-sonnet-3-5-no-tools` are identical documents
(φ = 1.000). Their six findings appear twice in the counts above. They are **one
reviewer**, which is why k=9 is the honest denominator.

## What the operator decides

1. Accept, split or reject each group — especially `G13`, which bundles distinct
   omissions, and `G8`, which may not belong in a findings tally at all.
2. Resolve the contested cluster. It is the only place reviewers directly
   contradict one another.
3. Confirm whether the duplicate pair was two submissions or one.
4. Verify the two checkable external claims: `G6b` (PushEvent payload) and `G21`
   (Events API retention). Both are single-reviewer, both would change the
   design, neither has been checked.

---

## Verification of the two external claims (2026-08-29)

Both were single-reviewer, both would change the design, neither had been
checked. **Both are correct.**

### G6b — `PushEvent` no longer carries commit messages: CONFIRMED

Checked against the live API on this repository's own pushes, not against a
changelog:

```
$ gh api repos/G-0-B/FLOSS/events --jq '[.[]|select(.type=="PushEvent")][0].payload|keys'
["before","head","push_id","ref","repository_id"]
```

No `commits` key. GitHub announced the removal on 2025-08-08, brownout-tested it
2025-09-08, shipped it 2025-10-07 — ten months before the anchor was written.
`GLM/F1` named the ship date correctly.

**But the finding is half right in a way that matters.** The spec put the root in
*two* carriers, and only one is dead:

| Carrier | Event | Status |
|---|---|---|
| Commit message | `PushEvent` | **DEAD** — no `commits` key at all |
| Tag name | `CreateEvent.payload.ref` | **ALIVE** — ref carried verbatim |

`CreateEvent` payload keys today:
`["description","full_ref","master_branch","pusher_type","ref","ref_type"]`.
`DeleteEvent` carries `ref` too, so deleting an anchor tag is itself externally
visible — a partial answer to `G6`'s tag-mutability attack.

Combined with `GROK/F3` (no tags exist; the CLI never creates them): **the
surviving carrier has never been used, and the carrier actually used at genesis
`fbaae97` witnesses nothing.** The spec's external-witness claim is now ❌ Blocked
rather than ⚠️ Specified.

### G21 — Events API retention cut to 30 days: CONFIRMED

90 → 30 days, effective **2025-01-30**, announced 2024-11-08. `GLM/F5` named the
date correctly. Added to the spec's Limits: a mirror that does not ingest within
30 days has nothing to ingest, so both anchor cadence and mirror-confirmation
cadence are bounded by that number.

### What this does to the merge groups

`G6` (7 findings, 6 reviewers) is **upgraded, not merely sustained**. The panel
argued the tag/firehose story was overstated; the actual position is worse than
any single reviewer stated — one carrier is dead, the other unexercised. `GLM`
supplied the decisive fact and was the only reviewer to name it. It is a
single-reviewer finding that outweighs the six-reviewer group it belongs to,
which is exactly the case for preserving minority findings rather than tallying
them.

Note also which reviewer this was: `glm-5-2-web-all-tool-use`, running with
`github`, `web` and `execution`. The two decisive external facts in the whole
corpus came from a tooled reviewer citing dated changelog entries, not from any
of the bare-chat reviewers. Suggestive for the tool-access hypothesis; still one
data point.
