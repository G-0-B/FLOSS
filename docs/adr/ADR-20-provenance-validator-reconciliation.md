# ADR-20: Provenance Validator Reconciliation — Evidence Vocabulary Drift and Ancestor Supersession

## Status
Accepted (operator, 2026-08-24) — D-A1 and D-B3 implemented; D-B1 still unbuilt.
Drafted 2026-08-23 as Proposed with no code, audited, then implemented on operator
approval. **Blast radius reclassified System → Substrate on 2026-08-25** following
external meta-audit; see the Meta-Audit Reclassification section.

## Date
2026-08-23 (implemented 2026-08-24)

## Truth Status
✅ Verified — both defects reproduced against the working tree, then fixed. D-A1
and D-B3 are implemented with regression tests; 267 tests pass. End-to-end proof:
the hook now lands claims. A Local `CodeChange` on
`packages/activity_log/provenance.py` produced
`[hook] claimed packages\activity_log\provenance.py → 01a0321a-2546-7fba-b67f-c8717d478060`
followed by a spawned consensus round — the first claim to land in the pilot's
history. A governed `AdrChange` now fails at `E_GOVERNED_PROVENANCE_REQUIRED`
instead of `E_SUBMIT_CLAIM_INVALID_PROVENANCE`, which is the consent-ref blocker
the audit predicted (Open Question 6), not a provenance failure.

⚠️ Specified — D-B1 (the audit disposition view) is unimplemented.

## Context

The provenance spine has been running in its pilot configuration (Claude hooks plus
the consensus gateway) since 2026-08-10. It has never landed a single claim.

`$HOME/.floss_agent/hook.log` (576 KB) records the full pilot history. Every hook
invocation completes: pre-write checkpoints are taken, post-write hashline
verification returns `VERIFIED`, and a signed provenance packet is created. Every
subsequent `submit_claim` is then rejected:

```
[hook] provenance packet EjHrNH9GOJcU8SChlt6yF37FFEUlI5oDByAcIQVGvZEE for packages\mcp_daemon.py
[hook] submit_claim error for packages\mcp_daemon.py: E_SUBMIT_CLAIM_INVALID_PROVENANCE: E_PROVENANCE_ARTIFACT_HASH_MISMATCH;E_PROVENANCE_EVIDENCE_REF_INVALID
```

Error tally across the log's lifetime:

| Error | Count |
|---|---|
| `E_SUBMIT_CLAIM_INVALID_PROVENANCE` | 54 |
| `E_PROVENANCE_ARTIFACT_HASH_MISMATCH` | 50 |
| `E_PROVENANCE_EVIDENCE_REF_INVALID` | 25 |
| `E_PROVENANCE_PRIOR_NOT_FOUND` | 4 |
| `E_PROVENANCE_ARTIFACT_MISSING` | 3 |

The rejection rate is 100%. The provenance record for the pilot period is empty not
because the hooks failed to fire, but because the validator rejected everything they
produced. This ADR names the two independent causes.

A prior diagnosis in the same session concluded that the hooks were not being
invoked at all. That conclusion was wrong and is retracted here: it rested on
looking for `hook.log` under `.agent-surface/` when `hook_post_write.py:43-44`
places it at `$HOME/.floss_agent/hook.log`.

### Defect A — a third, undocumented evidence-type allow-list

`docs/specs/provenance-packet.spec.md` records the v1.5 D3 widening as applied in
three places:

> **D3 — evidence-type extension.** `file`, `log`, `activity`, `source_chain`
> added to the evidence-root vocabulary, in this spec, in
> `provenance-packet.schema.json`, and in `EVIDENCE_TYPES` in
> `packages/orchestrator/claim_schema.py`.

All three are correct at this head. `provenance-packet.schema.json` carries the
ten-value enum, and `claim_schema.EVIDENCE_TYPES` (line 75) carries all ten with an
explanatory comment citing ADR-19.

A fourth allow-list exists and was not updated, because D3's author did not know it
was there — `packages/activity_log/provenance.py:564`:

```python
_EVIDENCE_REF_TYPES = {"spec", "test", "adr", "url", "commit", "provenance_packet"}
```

This constant is the one `_payload_entry_errors` actually enforces (line 594). A
packet using any D3 type is schema-valid, passes `claim_schema` validation, and is
then rejected by `validate_packet` with `E_PROVENANCE_EVIDENCE_REF_INVALID`.

This is the second instance of the same failure mode in this subsystem. The first
was `spec_gate.GATED_SURFACES`, a hardcoded tuple that had drifted from the
`gated_surfaces` field in `docs/specs/spec-registry.json` — where the registry field
turned out to be documentation-only and the tuple was the real authority. In both
cases a specification was edited, a nearby constant was treated as the
implementation of that specification, and a second constant elsewhere was the thing
with actual force.

### Defect B — ancestor hash mismatch is fatal, and supersession is unimplemented

`docs/specs/provenance-packet.spec.md` §Audit Disposition already anticipates the
staleness problem and resolves it:

> Strict packet validation and operator-facing daily audit are separate views.
> `validate_packet()` remains strict: if an artifact ref no longer hashes to the
> packet's recorded `sha256`, the packet is not valid current evidence.
>
> Daily Plane A audit MAY classify a strict `E_PROVENANCE_ARTIFACT_HASH_MISMATCH`
> as `superseded` instead of active `invalid` when the packet is historical
> evidence for mutable generated outputs or when a newer valid packet from the
> same agent covers the same claim/artifact surface.

Strict re-hashing of the packet under submission is therefore correct and intended,
not a defect. Two things around it are not.

**B1 — the supersession view does not exist.** The string `superseded` appears
nowhere in non-test code under `packages/`. The spec defines three operator-facing
audit statuses (`valid`, `superseded`, `invalid`); the implementation provides only
the strict boolean. The escape hatch the spec designed for exactly this situation
was never built.

**B2 — ancestor packets are held to current-truth standards.** `validate_packet`
follows the `p` prior chain by default (`_follow_prior: bool = True`, line 672) and
applies `_artifact_errors` to each ancestor. Lines 756-761:

```python
    # Ancestor artifacts may legitimately be gone (scratch probes, renames,
    # relocated intake). Only absence is downgraded; hash mismatch stays fatal.
    for problem in _artifact_errors(packet, root):
        if _is_ancestor and problem == "E_PROVENANCE_ARTIFACT_MISSING":
            warnings.append(problem)
        else:
            errors.append(problem)
```

The asymmetry is deliberate and documented: a missing ancestor artifact is
downgraded to a warning, a mismatched one stays fatal. The consequence was not
intended. Editing any file twice permanently invalidates every earlier packet naming
it, and because those packets remain in the `p` chain, they invalidate every future
packet from the same agent. The chain does not degrade — it dies at the first
re-edit and stays dead.

This is why the observed mismatches cluster on `packages/activity_log/provenance.py`
and `packages/mcp_daemon.py`, the two files edited most often during the pilot. A
freshly created packet hashes its own artifact correctly; a round-trip probe at this
head confirms `artifact_ref` → `_resolve_workspace_ref` → `sha256_file` agrees
exactly, and the workspace roots used by the hook (`REPO_ROOT.parent`) and the
gateway (`tools.py:408`, `_REPO_ROOT.parent`) both resolve to `C:\~shit`. The fresh
packet is fine. Its ancestors are what fail it.

The spec's own language argues against the current behaviour: superseded packets
"are preserved and reported, but they do not satisfy governed-claim evidence
requirements and must not be treated as current truth." Treating an ancestor's stale
artifact hash as a fatal error on a descendant's submission is precisely treating a
superseded packet as current truth — inverted, so that its staleness propagates
forward rather than being contained.

## Decision

⚠️ Specified — proposed, not implemented. Three changes, separable and independently
reviewable.

**D-A1 — collapse the evidence-type vocabulary to one authority.** Import the
evidence-type set in `provenance.py` from a single shared definition rather than
restating it. `claim_schema.EVIDENCE_TYPES` is the natural home; it is already
correct, already carries the rationale comment, and is already the set enforced at
claim-construction time. `_EVIDENCE_REF_TYPES` becomes an alias or is deleted. Any
future widening then has one edit site, and the spec's "added in three places"
phrasing becomes "added in one."

**D-B1 — implement the audit disposition view.** Provide the three statuses the spec
defines. Strict `validate_packet` is unchanged; the audit layer sits above it and
classifies a strict `E_PROVENANCE_ARTIFACT_HASH_MISMATCH` as `superseded` under the
two conditions the spec already names — mutable generated outputs, or coverage by a
newer valid packet from the same agent over the same claim/artifact surface.

**D-B2 — downgrade ancestor hash mismatch to a warning, symmetric with absence.**
⚠️ Superseded by D-B3 following the adversarial audit below; retained for the
record. Extend the existing `_is_ancestor` downgrade at line 758 to cover
`E_PROVENANCE_ARTIFACT_HASH_MISMATCH` alongside `E_PROVENANCE_ARTIFACT_MISSING`. The
justification is the same one already written in the comment above it and now
strengthened: an ancestor's artifact refs describe the workspace as it was, and the
descendant makes no claim about their current state. Strictness is retained where it
carries meaning — at depth 0, on the packet actually under submission, where a
mismatch means the submitter is claiming a hash the workspace does not have.

**D-B3 — stop running artifact validation on `p` ancestors at all.** Added
2026-08-23 in response to the audit, which was unanimous that D-B2 patches a
symptom. The spec's obligation for the `p` pointer is existence and continuity; it
says explicitly that `p` "does not consume the evidence-DAG recursion budget," a
narrower contract than the full `_artifact_errors` pass the implementation performs
on every ancestor. Validate `p` ancestors for existence, signature validity, and
sequence continuity only. Run `_artifact_errors` at depth 0 exclusively.

D-B3 subsumes D-B2: with no ancestor artifact pass, there is no ancestor hash
mismatch to downgrade, and the existing `_is_ancestor` special case for
`E_PROVENANCE_ARTIFACT_MISSING` becomes dead code that should be removed with it.
D-B3 is also the smaller behavioural claim — it aligns the implementation to the
spec rather than relaxing a rule the spec imposes.

## Consequences

Under D-A1, D3 becomes fully effective and packets may honestly cite `file`, `log`,
`activity`, and `source_chain` roots. ADR-19's evidence table, which motivated the
widening, stops having to flatten script output and live smoke runs into `url`.

Under D-B3, provenance chains survive ordinary editing. This is the change that
makes the spine usable at all: without it, the pilot's 100% rejection rate is
structural and no amount of correct hook behaviour can produce a landed claim.

The cost of D-B3 is a genuine reduction in what a valid packet asserts. Today a
validating packet implies its entire ancestry still hashes true — an assertion that
is strictly stronger, and which the pilot demonstrates is unsatisfiable in a live
workspace. After D-B3 a valid packet asserts that *it* hashes true and that its
ancestry is structurally intact and correctly signed. Historical artifact state
becomes the audit view's responsibility (D-B1), which is where the spec put it.

Neither of these is sufficient on its own to restore the spine. Governed
System/Substrate claims additionally require a resolvable
`consent_ref.decision_action_hash`, and per ADR-12 the current check accepts any
non-empty string without resolving it. D-A1 and D-B3 clear the provenance-side
rejections; the consent-side blocker is ADR-12's to close.

D-B1 and D-B3 land separately, D-B3 first. An earlier draft argued they were a
pair — that D-B3 without D-B1 drops the staleness signal rather than relocating it.
The audit rejected that argument 2-1 and it is withdrawn: the staleness condition is
observable from the packet store whether or not the reporting view exists, and
holding the usability fix hostage to a reporting surface is the kind of bundling
that leaves both unshipped.

## Open Questions For Review

Questions 3 and 5 were settled by the audit below and are marked accordingly.

1. **Blast radius. Open.** Filed as System — a cross-module change to validation
   behaviour, not to an invariant. The counterargument is that relaxing ancestor
   validation loosens a fail-closed governance gate, and `provenance_first` is a
   stated non-negotiable, which would make it Substrate (0.85, override forbidden).
   The distinction turns on whether "an ancestor's artifacts still hash true" was
   ever part of the invariant or is an implementation artifact of the strict walk.
   The audit split 4-1 for System with one non-answer; the dissent is recorded
   below. D-B3 weakens the Substrate reading further, since aligning code to the
   spec's stated `p` contract is not a loosening. Ratify explicitly at the gate.

2. **Does relaxing ancestor validation open a laundering path? Open, and this ADR
   does not close it.** An agent could submit a packet whose ancestry cites
   artifacts it has since rewritten. The signature chain and SAID digests are
   unaffected, so the *history* is not forgeable — but the artifact bindings in that
   history become unverifiable-in-place. The audit majority read this as hollow; one
   voter refused, on the grounds that the ADR never enumerates who reads ancestor
   artifact refs. That objection is correct. **Exit condition: enumerate every
   consumer of ancestor artifact refs and confirm none treats them as current
   evidence.** Until that list exists the question stays open.

3. **Should `p`-chain artifact validation run at all? Settled — no.** The audit was
   unanimous among voters who answered. The spec's `p` obligation is existence and
   continuity, narrower than the full `_artifact_errors` pass the implementation
   performs. This became D-B3, which supersedes D-B2.

4. **Is there a fourth allow-list? Open.** Defect A is the second instance of this
   pattern. A deliberate sweep for other constants that restate a specification —
   rather than another incidental discovery — is warranted before this closes.

5. **Are D-B1 and the B-track code change a pair? Settled — no.** The audit split
   2-1 against the pairing. Withdrawn; see Consequences.

6. **Does the consent-side blocker gate this ADR's value? Open, owned by ADR-12.**
   The audit was unanimous that D-A1 plus the B-track change is insufficient to
   land a governed claim while `entry_has_consent()` accepts an unresolved
   `decision_action_hash`. One voter proposed an `E_CONSENT_HASH_UNRESOLVED` code
   for the condition. Tracked here so this ADR is not mistaken for a full restoration
   of the spine.

## Adversarial Audit — 2026-08-23

Run through the reasoning-ensemble MCP in forced `ensemble` mode against the five
open questions above, with the prompt instructing voters to attack the ADR rather
than summarize it. Draft:
`docs/reviews/2026-08-24-adr20-adversarial-audit/synthesis.json`.

Six voters across five provider surfaces and six model families, satisfying the
≥3-surface / ≥4-family diversity policy: `groq/openai/gpt-oss-120b`,
`groq/qwen/qwen3.6-27b`, `huggingface/deepseek-ai/DeepSeek-V4-Flash`,
`mistral/devstral-small-latest`,
`nvidia/nvidia/llama-3.3-nemotron-super-49b-v1`, `openrouter/openai/gpt-4o-mini`.

**The synthesizer reported this as Tier-1, 6/6 unanimous. That label is wrong**, and
the error matters more than any single finding. Reading the individual voter
responses rather than the synthesis:

- `groq/qwen/qwen3.6-27b` did not answer. Its 2291-character response restates the
  prompt back as a structured summary and reaches no position on any of the five
  questions. It was embedded and clustered as agreement.
- `groq/openai/gpt-oss-120b` returned 359 characters — a fragment, roughly a sixth
  the length of the others — and it **dissents on Q1**, arguing D-B2 "relaxes a
  fail-closed invariant that the substrate declares non-negotiable" and that any
  later edit "instantly re-opens the whole p-chain for the originating agent."
- Q5 splits three ways among the three voters who reached it: `mistral` calls the
  pairing "rationalization," `openrouter/gpt-4o-mini` calls it "not sound," and
  `nvidia/nemotron` calls it "mechanistically justified."

Clustering runs on whole-response embeddings, so responses that agree on tone,
vocabulary and structure cluster together even when they hold opposite positions on
a specific sub-question, and a response that answers nothing at all clusters with
everything. The similarity matrix bears this out: the three tightest pairs (0.953,
0.954, 0.957) are deepseek/mistral/gpt-4o-mini, which are the three most similarly
*formatted* answers, not the three most similarly *concluded* ones. **A 100%
largest-cluster fraction on an adversarial prompt should be read as a signal to
open the individual responses, not as confirmation.** This is a defect in the
ensemble's Tier classification, not in this ADR, and it is filed here because it
was found here.

Findings, taken from the individual responses:

**Q1 — blast radius.** *(This tally was corrected on 2026-08-26; see "Correction
to the Q1 tally" below. It originally read "4 System, 1 Substrate, 1 no-answer",
which is not what the raw responses say.)*

There is no majority here to state. Read from `voter_responses[]`, exactly one
voter answered **System** and exactly one answered **Substrate**; the other four
did not produce a classifiable verdict. What every voter who expressed any view
on D-B2 shared was opposition to it.

The System argument, made by `huggingface/deepseek-v4-flash`, is that blast
radius follows which invariant a change alters, not whether a nearby label reads
"non-negotiable": depth-0 strictness is untouched, so the `provenance_first`
core — a current packet must carry valid current evidence — survives, and only
historical artifact consistency relaxes. It is recorded here because it is the
strongest version of the position this ADR originally took, not because it
carried a majority. Note that D-B3, which the same audit prefers, makes the
question substantially easier: aligning the implementation to the spec's stated
`p` contract is not a loosening at all.

**Q2 — laundering. Split, and the split is the useful part.** The majority reads the
worry as hollow: no downstream consumer treats ancestor artifact refs as current
evidence today, the `p` chain is used for continuity and signature verification, and
the new packet's own depth-0 hash stays strict. `mistral` refuses to close it on
those terms — "Missing: ADR doesn't identify who/what reads ancestor artifact refs."
That is correct and this ADR does not close it. Open Question 2 stands, with the
enumeration of ancestor-ref consumers as its explicit exit condition.

**Q3 — over-validation. Unanimous among voters who answered, and this changed the
ADR.** D-B2 is a symptom patch; the root defect is that the implementation performs
a full artifact pass on ancestors where the spec asks only for existence and
continuity. D-B3 above is the result.

**Q4 — sufficiency. Unanimous: not sufficient.** Independently of the prompt's own
mention, multiple voters land on the same next blocker — `entry_has_consent()`
checks that `consent_ref.decision_action_hash` is a non-empty string and never
resolves it, so governed System/Substrate claims will keep failing after D-A1 and
D-B3 land. `mistral` proposes an `E_CONSENT_HASH_UNRESOLVED` error code for the
condition. That work belongs to ADR-12, not here, but this ADR should not be read as
restoring the spine on its own.

**Q5 — sequencing. 2-1 against the pairing.** The majority holds that D-B1 and the
B-track code change are independently landable and that bundling them is
rationalization. This is accepted: the pairing argument is withdrawn. D-B1 (the
audit view) and D-B3 (the validation-scope correction) land separately, D-B3 first,
since D-B3 is what makes the spine capable of landing a claim and D-B1 is the
reporting surface for a condition that will still exist after it.

## Implementation Record — 2026-08-24

D-A1 and D-B3 landed on operator approval. D-B1 was not built.

**D-A1.** `provenance.py` imports `EVIDENCE_TYPES` from
`packages.orchestrator.claim_schema`; `_EVIDENCE_REF_TYPES` is now bound to it
rather than restating it. No circular-import risk — `claim_schema` imports nothing
from `packages/`, and `orchestrator` does not import `activity_log`. Regression
test parametrized over all four D3 types, which also asserts the identity
`provenance._EVIDENCE_REF_TYPES is EVIDENCE_TYPES` so a future re-fork of the
literal fails loudly.

**D-B3, wider than drafted.** The draft scoped it to the artifact pass. Landing
that alone cleared every `E_PROVENANCE_ARTIFACT_HASH_MISMATCH` and left
`E_PROVENANCE_EVIDENCE_REF_INVALID` still failing every submission. Walking the
chain found why, and it is worth recording because it settles the scope question
the draft left open:

> Chain position 51 carries an evidence ref whose `sha256` is **63 characters** —
> a dropped leading zero. The packet is signed. It cannot be repaired: correcting
> the field breaks the signature. Every descendant of position 51 was therefore
> permanently unable to submit, and there was no action any agent could take to
> recover.

That is the same failure shape as the artifact staleness, from a different
direction, and it demonstrates that scoping only the artifact pass was still too
narrow. Depth-0 now owns three passes, not one:

- `_artifact_errors` — artifact refs
- `_payload_entry_errors` — the per-entry field contract
- `_recursive_evidence_errors` — the evidence DAG

Ancestors retain signature verification, SAID/digest, version, envelope type,
non-empty payload, sequence continuity, and the duplicate-chain-position fork
check. That is the "existence, signature validity, and sequence continuity"
contract D-B3 named, now applied consistently rather than to one pass.

The general principle, which the draft did not state: **a signed historical packet
cannot be corrected, so any contract enforced against ancestors is a contract that
can permanently and irrecoverably kill a chain.** Enforcement belongs at the point
of authorship, where a failure is actionable.

**Test changes.** `test_deleted_ancestor_artifact_warns_but_does_not_fail_descendant`
previously asserted the ancestor `E_PROVENANCE_ARTIFACT_MISSING` warning; under
D-B3 ancestor artifacts are not inspected at all, so it now asserts neither error
nor warning. Its depth-0 strictness assertion is unchanged. Added
`test_edited_ancestor_artifact_does_not_fail_descendant`, which covers the actual
defect — mutation, not deletion — and confirms depth 0 still rejects a stale hash.

**Not done.** D-B1 remains unbuilt, so there is currently no `superseded` reporting
for the historical packets this change stops failing on. Open Questions 1, 2, 4 and
6 all remain open; in particular Question 2's exit condition (enumerate every
consumer of ancestor artifact refs) was not satisfied before landing — the change
went in on the audit majority's reading plus operator approval, not on a completed
enumeration. That is a known, accepted gap, not an oversight.

## D-B3 Addendum — Chain Gaps Are Enumerated, Not Concealed Or Refused

Operator-approved 2026-08-24, landed in `61cdd5c`. This settles Open Question 2.

D-B3 as first landed said nothing about an *unreachable* ancestor, only about
artifact refs. A parallel agent then closed the resulting hole in the opposite
direction (`b0de2fe`), making a missing ancestor fatal at every depth on the
strength of the spec sentence "a `p` reference to a nonexistent prior packet is
invalid." Both changes are individually defensible. Together they moved the spine
from 100% rejection to working to 100% rejection again inside an hour, decided
twice in opposite directions by two agents who could not see each other.

The framing both missed: **a signed packet cannot be re-derived once lost.** A
hole is therefore permanent, and any rule that refuses a chain containing one
refuses that agent forever. Meanwhile the property actually being protected is
not that holes be impossible — it is that they be *undeniable*.

Sequence numbers are per-agent and monotonic, so a deleted packet leaves an
arithmetic gap whether or not its file survives. The walk now uses that:

| Condition | Verdict |
|---|---|
| Expected slot occupied, child points elsewhere | `E_PROVENANCE_CHAIN_FORK` — fatal. A rewrite. |
| Expected slot empty | Enumerate the exact sequence numbers, resume below the gap, keep verifying |
| Prior exists further back, skipped slots **empty** | Enumerate — the packets are gone |
| Prior exists further back, any skipped slot **occupied** | `E_PROVENANCE_SEQUENCE_DISCONTINUOUS` — fatal. Bypassed, not lost. |
| Chain does not reach sequence 0, or genesis is not sequence 0 | Fatal |

The rule in one line: **enumerate what is lost, refuse what is merely bypassed.**
Gaps surface as `E_PROVENANCE_CHAIN_GAP:<n>,<n>` in `warnings`, enumerated rather
than summarised, so an auditor can name exactly which packets to go looking for.
Silence was the actual defect in the original behaviour; refusal was the defect in
its replacement.

### What this found in the live chain

Running it against identity `DkuYPguG98HM2nyR` (97 packets, sequences 0..100)
surfaced three defects, none introduced by this work and none previously visible:

1. **Four packets absent** — sequences 3, 36, 37, 39. Now enumerated.
2. **Sequence 2 points at sequence 0** while sequence 1 is present on disk. A
   bypass, not a loss. Fatal under the rule above.
3. **Sequence 5 carries `p: null`**, claiming to be genesis at position 5. The
   chain asserts a false origin.

Defects 2 and 3 are unrepairable — the packets are signed, so correcting a field
breaks the signature. The remedy is **identity rotation**: start a fresh chain at
sequence 0 and retain the existing packets as an audit record with their defects
enumerated. That is an operator action and has not been taken here. Until it is,
this identity cannot produce a valid governed claim, and that is the correct
outcome rather than something to weaken validation for.

The likely cause is the concurrency defects fixed in the same sweep — the
`_acquire_lock` stale-reclamation bug and the daemon singleton races — which is
consistent with holes and doubled origins appearing under concurrent writers.

## Meta-Audit Reclassification And Trust Boundary — 2026-08-25

Four independent external audits (ox-alpha, Gemini, DeepSeek, Mistral) were
aggregated by a review board into a meta-audit. Its rulings are recorded here, and
two of them go against positions this ADR took.

### Blast radius is Substrate, not System

This ADR filed the change as System. Three of four auditors, the review board, and
the original dissenting ensemble voter say **Substrate** (0.85, override-forbidden).
The board's reasoning, which I accept:

> the question is whether the change alters what the *governance substrate* will
> accept for governed claims. It does — by design. A fail-closed gate being relaxed
> is precisely the class of change override-forbidden review exists for. That the
> change is also well-motivated doesn't downgrade its blast radius.

Open Question 1 is closed as **Substrate**. Worth recording that
`groq/openai/gpt-oss-120b` reached this conclusion first, in a 359-character
fragment — truncated mid-sentence — that the synthesizer clustered as agreement.

It was not, however, the lone dissenter, as this ADR originally claimed.
`mistral/devstral-small` opened its answer `**1. BLAST RADIUS: Substrate (0.85,
override forbidden).**` and was filed on the System side, and
`nvidia/nemotron-super-49b` labelled its answer System while its own stated
rationale — "Agree with the counterargument; D-B2 poses a non-negotiable risk to
`provenance_first`" — is the Substrate position. See "Correction to the Q1 tally"
below. The conclusion this section reaches is unchanged and better supported than
when it was written.

### Open Question 2 is closed, against this ADR's reasoning

The ADR asked whether enumeration truly makes a hole undeniable, and reasoned that
a head's own signed `s` could not be lowered. **That reasoning was incomplete and
the conclusion was wrong.** The attack does not lower any sequence number:

> **Wholesale head truncation.** An adversary with write access deletes every
> packet above sequence *n* and presents *n* as current. Enumeration finds gaps
> only relative to the highest sequence still present, so there is no gap to find.
> Nothing inside a self-signed chain distinguishes truncation from an agent that
> simply has not written since *n*.

All four audits identified this independently; the board rates it Critical/P0 and
calls it the highest-confidence finding in the corpus. **Enumeration is undeniable
only against an adversary who cannot delete the evidence of deletion.**

The bypass-then-delete ordering exploit (Open Question 2's second half) is likewise
confirmed: occupancy is evaluated at validation time, so bypassing a live packet and
deleting it afterwards converts a fatal discontinuity into an enumerated gap.

Both are the same missing primitive — nothing outside the packet store witnesses
what the store contained — and both are now documented as known limits in
`docs/specs/provenance-packet.spec.md`.

### Trust boundary, stated explicitly

Flagged P0 by the board because leaving it unstated lets the spine read as
stronger than it is. **The provenance spine defends against a buggy-but-honest
writer. It does not defend against control of the packet store, host compromise,
or theft of the signing key.** A single Ed25519 key sits unencrypted on disk;
whoever holds it can author any history they like, and whoever can write to
`.agent-surface/provenance/` can truncate it. Every integrity claim in ADR-20 and
in the packet spec is scoped to the honest-writer model until an external anchor
exists.

### Retrospective vote re-tally (M-3)

The board asked whether decisions resting on the ensemble synthesizer should be
re-tallied from raw `voter_responses[]`, since that synthesizer mislabels dissent
as agreement. For this ADR the re-tally was performed and is recorded in the
Adversarial Audit section above. The synthesizer's "Tier-1, 6/6 unanimous" was
false. Other tiered decisions in the repository have not been re-tallied and
should be.

### Correction to the Q1 tally (2026-08-26)

**A hand re-tally that reads a synthesis for verdict tokens reproduces the same
failure at one remove, and this ADR did exactly that.** The correction is
recorded here rather than by rewriting the record, because the original figure
was cited and a silent edit would leave a citation pointing at something that
never existed.

This ADR recorded Q1 as **"4 System, 1 Substrate, 1 no-answer"** with
`groq/openai/gpt-oss-120b` as "the lone dissenter." Re-read against
`docs/reviews/2026-08-24-adr20-adversarial-audit/synthesis.json`:

| Voter | What its text actually says |
|---|---|
| `huggingface/deepseek-v4-flash` | **System**, explicit and argued. |
| `mistral/devstral-small` | **Substrate.** Opens `**1. BLAST RADIUS: Substrate (0.85, override forbidden).**` Filed on the System side. |
| `nvidia/nemotron-super-49b` | Labelled **System**; rationale reads "Agree with the counterargument; D-B2 poses a non-negotiable risk to `provenance_first`" — the Substrate position. Label and reasoning contradict. |
| `groq/openai/gpt-oss-120b` | Truncated at 359 chars mid-sentence. Substrate-leaning, but emits no verdict token. |
| `openrouter/gpt-4o-mini` | Never uses the System/Substrate vocabulary at all. Opposes D-B2 on other grounds. |
| `groq/qwen3-27b` | No answer. A bare unclosed `<think>` restatement of the prompt, 2291 chars. Counted as a converged voter. |

So the honest tally is **1 explicit System, 1 explicit Substrate, and four
responses that cannot be classified** — one of them not an answer at all. There
was never a 4-1 majority to overrule. The original figure manufactured one by
reading a synthesis rather than the responses, then attributing a verdict to
voters that had not given one.

Three things follow.

1. **The Substrate reclassification is unaffected and better supported.** It was
   decided on the argument, and the raw responses contain more support for it
   than the ADR credited, not less.
2. **`groq/qwen3-27b` and `groq/openai/gpt-oss-120b` were non-functional across
   the whole 2026-08-24 campaign** — an unclosed reasoning block in 5 of 5 runs
   and a mid-sentence truncation in 5 of 5, at 212/359/727/1290/1466 characters
   against 2000-3200 for peers. Two of six voters produced no positions, so the
   "≥3 provider surfaces / ≥4 model families" independence bar was met on paper
   by voters that did not vote. `degenerate_voters()` in
   `packages/reasoning_ensemble/synthesizer.py` now flags both shapes.
3. **A verdict token is not a vote.** `nvidia/nemotron-super-49b` labelled itself
   System while arguing Substrate; `openrouter/gpt-4o-mini` argued a position
   without ever using the vocabulary. Any future re-tally must read the argument,
   not scan for the word — which is also why the replacement for the ensemble is
   a structured per-question ballot rather than a better clustering threshold.

### Accepted but not implemented here

External anchoring (P0-strategic), closing the ADR-12 consent gate, replacing the
ensemble aggregation, `filelock` adoption, the KERI-versus-DSSE fork decision, and
identity rotation with a signed lineage statement. Identity rotation was
challenged by one auditor as "not standard practice"; the board upheld it, on the
grounds that witnessing prevents future concealment but cannot repair an existing
false-genesis packet.

### Note on the audit inputs

Two of the four external audits carried confabulation-suspect citations — RFC
numbers, ratification dates and arXiv IDs that could not be corroborated. The
board struck those citations while retaining the findings, which stood on
independent reasoning. The board's own process finding applies to this project
directly: **AI-authored audits entering the governance pipeline should be held to
the same truth-status discipline as anything else, with citation-resolvability
required for a Verified tag.**

## Evidence

- `$HOME/.floss_agent/hook.log` — pilot history, 576 KB, error tally above.
- `packages/activity_log/provenance.py:564` — `_EVIDENCE_REF_TYPES`, six values.
- `packages/activity_log/provenance.py:594` — the enforcement site.
- `packages/activity_log/provenance.py:672` — `_follow_prior` default.
- `packages/activity_log/provenance.py:756-761` — the ancestor downgrade asymmetry.
- `packages/orchestrator/claim_schema.py:75` — `EVIDENCE_TYPES`, ten values.
- `docs/specs/provenance-packet.schema.json` — evidence-type enum, ten values.
- `docs/specs/provenance-packet.spec.md` §Audit Disposition — the supersession policy.
- Absence check: `superseded` does not occur in non-test code under `packages/`.

## Related

- ADR-15 — author–provenance binding in the integrity zome. Different layer: ADR-15
  governs Plane B zome validation, this ADR governs the Plane A packet validator.
- ADR-19 — the evidence table that motivated the D3 widening.
- `docs/specs/provenance-packet.spec.md` — the contract this ADR proposes correcting
  the implementation against. Note that D-A1 and D-B2 are implementation corrections
  toward the existing spec, not spec changes; D-B1 implements a spec section that
  was never built.
