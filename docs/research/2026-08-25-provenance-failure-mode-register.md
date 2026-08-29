# Failure-Mode Register — Provenance Spine Repair, 2026-08-10 → 2026-08-25

**Status:** ✅ Verified — every entry is a defect that actually shipped and was actually
found, with the commit that introduced it and the commit that closed it.
**Authored by:** Claude Opus 5 (`claude-opus-5`).
**Scope:** the PR #41 repair sequence — ADR-20, the reuse gate, the post-write hooks,
and the reasoning-ensemble aggregation that shaped ADR-20's own decision.

This is not a changelog. It records the *shapes* of the mistakes, because the shapes
repeated and the individual fixes did not stop them. Fourteen commits, eleven review
rounds, and every single defect was found by an external reviewer rather than by the
repository or by its author.

---

## 1. The headline number

| | |
|---|---|
| Defects found by external review (Codex on PR #41) | **all of them** |
| Defects found by the author before review | 0 |
| Defects found by the repository's own gates | 1 (CI green set, and only because the author had not been running it) |
| Rounds where a fix introduced the next round's defect | 4 |

That last row is the important one. Four times, the commit that closed a finding
opened the next. This is not a story about carelessness on individual lines; it is a
story about a small number of recurring shapes.

---

## 2. Failure modes, by frequency

### FM-1 — Coercion standing in for validation

**Instances: 5.** `str(x).strip()` and `int(x)` were used as though they validated
their inputs. They do not; they *succeed* on inputs that should fail.

| Site | What passed that should not have |
|---|---|
| `reuse.candidates[].name` | `{"name": 7}` — `str(7)` is non-empty |
| `reuse.reviewer.outcome` / `.date` | `{"outcome": 7, "date": 20260825}` |
| `reuse.candidates[].probe.date` | non-string dates |
| `reuse.search_date` | `20260825` — `str()` gives `"20260825"`, which `date.fromisoformat` accepts as 2026-08-25 |
| `reuse.evidence_window_days` | `"999999"` and `999999.9` widen the freshness gate; `"soon"` raises out of the audit |

**Why it kept happening:** each fix was written as a local repair to the field named
in the finding. The author fixed `name` typing and then, in the same function one
level down, wrote `str(reviewer.get(key, "")).strip()` for `outcome` and `date`.

**What finally worked:** one shared `_iso_date_problems(label, value)` covering all
three date fields at once, checking type before shape and shape before parse. Note
`bool` is an `int` in Python and stringifies to `"True"` — it needs an explicit
exclusion.

**Rule:** if a check calls `str()` or `int()` on untrusted input before comparing,
it is a parser, not a validator. Validate the original type first.

---

### FM-2 — Naming the conclusion instead of showing the work

**Instances: 4.** A gate advertising evidence accepted an assertion *that* evidence
existed.

| Site | Satisfied by |
|---|---|
| `reuse.reviewer` (tier-2 independent review) | any prose, e.g. `"done"` |
| `reuse.candidates[].probe` | any string not starting with `not_probed` — so `"done"`, `"pending"`, `"TBD"`, and `"not probed: unavailable"` (space, not underscore) |
| `probe: {"status": "passed"}` | status alone, with no `detail` and no `date` |
| Claim evidence `{"type": "test", "ref": "hashline:SKIPPED"}` | a verification that explicitly did not run |

**Why it kept happening:** every fix replaced a *negative* test (reject this list of
bad words) with a slightly better negative test. A negative test can always be evaded
by a word not on the list.

**What finally worked:** positive assertion with substance behind it. A probe counts
only as `probed: <text>` or `{"status": "passed", "detail": <non-empty>, "date": <ISO>}`.
A reviewer record is an object naming surfaces, families, outcome, date, and a
`record` path that must resolve to a regular file inside the repository.

**Rule:** never gate on the absence of a bad marker. Require a positive one, and
require it to carry payload — a bare `probed:` prefix is the same defect as `"done"`.

---

### FM-3 — Several authorities for one vocabulary

**Instances: 6.** A specification was edited; a nearby constant was treated as its
implementation; a *different* constant elsewhere turned out to have the force.

1. `spec_gate.GATED_SURFACES` vs the registry's `gated_surfaces` field — the registry
   field was documentation only, the tuple was real. Drifted when hooks moved out of
   `scripts/` and four registry entries went silently unenforced.
2. The v1.5 D3 evidence-type widening reached the spec, the JSON Schema, and
   `claim_schema.EVIDENCE_TYPES`, and missed `_EVIDENCE_REF_TYPES` in `provenance.py`
   — the set `validate_packet` actually enforced. **This single miss caused a 100%
   claim rejection rate for the entire pilot.**
3. Candidate field types declared in the schema, not enforced in code.
4. `reuse.reviewer` tightened to an object in code while the schema still declared a
   string — for one commit, no value could satisfy both.
5. The registry's own schema had `additionalProperties: false` over three keys while
   entries carried `tier` and `reuse` — the canonical registry was invalid against its
   own schema.
6. `probe` accepted as an object by the probe rule and rejected as a non-string by the
   generic field rule, in the same pass.

**What finally worked:** a test file asserting schema and enforcement agree —
`scripts/tests/test_spec_gate_reuse_contract.py` — and, critically, writing those
assertions *generically*: "every key any entry uses must be declared" rather than
"`tier` and `reuse` must be declared". The instance-shaped version of that test was
written first and missed the very next instance.

**Rule:** when a spec and code both describe a rule, a test must assert they agree,
and that test must be written over the general property, not the instance just fixed.

---

### FM-4 — Fixing one reader of a structure and not its sibling

**Instances: 3, all in `packages/activity_log/provenance.py`.**

- `_slot_is_genuinely_occupied` was added so unsigned garbage could not fake a fork.
  That validity probe read only the *first* path per slot, because `_sequence_index`
  used `setdefault`. A decoy whose filename sorted earlier became the sole occupant,
  the slot read as empty, and a bypass escaped the fork check. **The fix created the
  hole.**
- Fixing `_sequence_index` to retain every occupant left `chain_index` — built from
  the same scan, keyed on each packet's internal `d` — as a last-write-wins dict
  comprehension. A decoy copying a genuine ancestor's digest replaced its path.
- Changing `_sequence_index` to lists broke two call sites that still indexed it as a
  scalar, caught only by running the tests.

**Rule:** when a scan populates more than one index, changing one is a change to all
of them. Grep for every consumer before editing the producer.

---

### FM-5 — Tests too narrow to fail

**Instances: 3.**

- `test_a_structured_probe_counts` asserted only the absence of the `"direct probe"`
  message. It passed while the value was being rejected on a different line. Fixed by
  asserting `fails == []`.
- The first decoy test aimed at the immediate prior and **passed against the live
  bug**, because the first hop resolves by filename and only deeper ancestors go
  through `chain_index`. It had to be re-aimed at genesis to reproduce.
- The guard written specifically for schema-versus-enforcement drift checked the
  reuse block's schema and never the registry's own.

**Rule:** a regression test must be seen to FAIL against the unfixed code. Every one
of these was written after the fix and passed immediately, which felt like
confirmation and was not.

---

### FM-6 — Running a different verification than the gate runs

**Instance: 1, and it turned CI red.**

The author ran `pytest packages/ scripts/tests` for the whole session. CI's required
green set is `packages/ tests/ scripts/tests/`. 490 local passes against a directory
that gates the PR and was never executed once. The break — a registration-guidance
string whose exact shape a test pinned — would have been caught locally by the correct
command.

**Rule:** run the gate's command, not an approximation of it. It is written in
`.github/workflows/python-ci.yml` under `GREEN_PATHS`.

---

### FM-7 - A borrowed shape read as borrowed compatibility

The packet envelope borrows KERI's field names, its SAID dummy-character algorithm,
its version-string shape, and its code letters at CESR-correct lengths. Every one of
those is a real, deliberate borrowing. None of them makes the packets CESR primitives.

The encoding underneath diverges: CESR prepends pad bytes *before* base64 conversion
("mid-padding"), and this envelope base64-encodes the raw value, strips the trailing
`=`, and prepends the code. Both produce 44 characters. They are different 44
characters, and a conforming CESR decoder reading ours does not raise - it returns a
plausible 32 bytes that are a two-bit shift of the true value.

```
raw   = bytes(range(32))
here  = EAAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8
CESR  = EAABAgMEBQYHCAkKCwwNDg8QERITFBUWFxgZGhscHR4f
```

Two smaller divergences travel with it: JCS sorts keys, so the version string is not
at the head of the frame where a KERI stream parser looks for it, and signatures live
inside the body and are computed over the body with `sigs` emptied, where KERI signs
the serialized event and attaches signatures outside it.

The repository is internally consistent - `_b64url_decode` is the exact inverse of
`_b64url_encode`, so we always read back what we wrote, and nothing is corrupted
today. What was missing was any statement that outside readers cannot do the same.
The shipped schema had carried "Code correctness UNVERIFIED - see spec section
9.1/9.2/9.4" against a spec with no section 9, so the question had been *asked*, in
writing, and left open long enough to stop being read as a question.

**Rule:** when an artifact borrows a standard's vocabulary, the divergences must be
written down at the same time, in the same document, and pinned by tests that assert
the divergence. Silence about a divergence is indistinguishable from a compatibility
claim. The tests in `packages/activity_log/tests/test_keri_divergence.py` fail if
someone makes the envelope CESR-correct, which is the intended signal that a
substrate-class migration - every SAID, identifier and signature in the chain - has
begun.

## 3. Coordination and process failures

### CF-1 — The same governance question decided twice, in opposite directions, within an hour

`18d9d9a` scoped ancestor artifact checks to depth 0 and the spine started landing
claims. About an hour later `b0de2fe`, by a parallel agent on the same branch, made
missing ancestors fatal at every depth on the strength of the spec sentence "a `p`
reference to a nonexistent prior packet is invalid." The spine returned to 100%
rejection the same day.

Both changes were individually defensible. Neither agent could see the other. The fact
neither had stated: **a signed packet cannot be re-derived once lost**, so a hole is
permanent and any rule refusing chains containing one refuses that agent forever.

**Insight that resolved it:** the property worth protecting is not that holes be
*impossible* — it is that they be **undeniable**. Sequence numbers are per-agent and
monotonic, so a deleted packet leaves an arithmetic gap whether or not its file
survives. **Enumerate what is lost; refuse what is merely bypassed.**

### CF-2 — Diagnosis anchored on a wrong path

A full diagnostic pass concluded "Claude Code is not invoking project hooks in this
session" and reasoned at length about hook approval in non-interactive sessions. The
hooks were firing the whole time. `hook.log` is at `$HOME/.floss_agent/hook.log`, per
`hook_post_write.py`, not under `.agent-surface/` where it was looked for. The real
defect — a 100% `submit_claim` rejection rate — was visible in the file the whole time.

**Rule:** before concluding a component is not running, find where it writes and read
that, from the source rather than from expectation.

### CF-3 — The minority was right and got outvoted

The 2026-08-23 ensemble audit split 4-1 on blast radius. The dissenter,
`groq/openai/gpt-oss-120b`, argued Substrate in a 359-character fragment that the
synthesizer clustered as agreement. The author *caught* the mislabeling, *recorded*
the dissent, and then filed System anyway. Two days later an external meta-audit
overturned it to Substrate on exactly the dissenter's reasoning.

**Rule:** recording a dissent is not the same as weighing it. A minority position that
survives scrutiny is evidence, not noise — especially when the aggregation mechanism is
known to suppress it.

### CF-4 — Aggregation that mistakes formatting for agreement

The synthesizer reported "Tier-1, 6/6 unanimous" when one voter answered nothing at
all, one dissented on the central question, and a third question split three ways.
Clustering runs on whole-response embeddings, so shared tone and structure outrank
opposed conclusions, and an empty answer clusters with everything. The similarity
matrix confirmed it: the tightest pairs were the three most similarly *formatted*
answers, not the three most similarly *concluded*.

**Rule:** a 100% largest-cluster fraction on an adversarial prompt is a signal to open
`voter_responses[]`, never confirmation. Check response LENGTH — one far shorter than
its peers is usually a truncation or non-answer counted as a vote.

**Quantified 2026-08-25.** This is worse than a bad run. All six syntheses in
`.agent-surface/reasoning/ensemble/` report `largest_cluster_fraction = 1.0` with an
empty minority set, across four prompts written to provoke dissent. The lowest
off-diagonal cosine similarity in the entire corpus is **0.791**, against a clustering
threshold of **0.75**. Not one pair, in any run, has ever fallen below the threshold -
a single cluster was the only reachable outcome, so the tier was never a finding about
the voters. Raising the threshold does not repair it: at 0.79 it still separates
nothing, and by 0.90 it splits on register rather than on claims.

`separation_diagnostics()` now marks such a run `E_CONSENSUS_NOT_MEASURED` and the
writeup leads with "This run did not measure consensus ... Do not cite this run as
corroboration". The threshold was left at 0.75 on purpose - a tuned-looking number
would hide the defect. Measuring agreement properly requires claim-level extraction,
which is a different design and still unbuilt.

### CF-5 — Skepticism defaulting to rejection under missing tool access

A meta-audit struck several citations as "confabulation-suspect" using a plausibility
heuristic — precise dates and version numbers read as hallucination markers — rather
than attempting retrieval. A later layer with live access reported them real. The
heuristic is a reasonable prior for a reviewer *without* tool access; applied without
the access it is a rejection machine.

**Rule:** before striking a claim as unverifiable, attempt retrieval. Only strike if
retrieval fails or contradicts. "Could not retrieve" and "does not exist" are different
findings and must be labelled differently.

### CF-6 - A decision inherited from a resemblance

The instruction was "we definitely want keripy, right? because Holochain uses it."
Holochain does not use KERI, ACDC, or CESR anywhere: a code search across
`holochain/holochain` returns zero, and the repository's own built zomes (hdi 0.7.1 /
hdk 0.6.1) use only `agent_info()`, `AgentPubKey`, and `ActionHash`. Holochain has its
own identity model - a per-install Ed25519 keypair in lair-keystore, a `holo_hash`
`AgentPubKey`, an Action source chain, and DeepKey for rotation. The two systems solve
the same problem with independent, non-interoperable designs, which is exactly why one
reads as the other.

The repository's own KERI-Holochain bridge is not a counterexample. `identity_integrity`
is excluded from the Cargo workspace as a pre-migration dev artifact, absent from
`dna.yaml`, and its validation carries the literal comment "TODO: Actual cryptographic
verification would happen here" while checking only that signature byte vectors are
non-empty. The corresponding spec was archived.

The premise being false does not make keripy the wrong choice - witness receipts and
pre-rotation are real answers to the head-truncation attack. It makes "because
Holochain uses it" the wrong *reason*, and a stated reason is what a later reader
audits the decision against.

**Rule:** verify the premise of a dependency decision before designing against it,
especially when the premise is a resemblance between two things that solve the same
problem. Record the reason that actually holds, not the one that motivated the ask.

### CF-7 - A reuse gate that fires at registration, not at design

This repository has an ADR-18 prior-art gate: adopt before extend before compose
before build, with tier-2 work requiring an independent review. During this session
that gate was hardened four times - malformed tiers stopped exempting entries,
non-boolean `emergency` stopped waiving the reuse block, future dates stopped
passing as evidence.

In the same session, with the ensemble's clustering defect measured, the response
was to start designing a replacement from scratch: per-question ballots, an
admission gate, a dissent-preserving tally. No prior-art search was run. The gate
did not fire, and it could not have: `spec_gate --check` inspects the registry when
a file is registered, which is long after the design decision is made.

The search, run afterwards, found an active literature that changes the design and
contains two results that contradict beliefs this repository operates on - that
model-family diversity buys independence, and that a panel is better than its best
member. See `2026-08-26-ensemble-aggregation-prior-art.md`.

**Rule:** the reuse question belongs at the moment a design starts, not at the
moment an artifact is registered. Before writing a design for anything that sounds
like a solved problem, search first and record what was found - including "nothing
fits", which is a finding and not a formality. A gate that only inspects artifacts
will always catch the file and miss the choice.

### CF-8 - Evidence that only works for the author

Two instances, one hour apart, both found by verification rather than by review.

**The path.** ADR-20 cited its reuse reviewer as a file under
`.agent-surface/reasoning/ensemble/`. That path was unresolvable from the repository
twice over: `.agent-surface` sits at the workspace root, one level above FLOSS, and
the directory is gitignored. It survived because `_reviewer_problems` -- and the
record-resolution guard inside it -- runs only for `tier == 2`, and the entry is
tier 1. Running the guard against the old value directly returns "does not exist";
the gate would have caught it the moment it applied, and it never applied.

**The hash.** Fixing that by copying the file into the repository produced the same
failure one layer down. `.gitattributes` carried `*.json text eol=lf`, so the commit
rewrote 200,104 CRLF bytes to 193,821 LF bytes while the record README published the
CRLF sha256 as the file's integrity claim. The evidence would have failed its own
hash in any clone. Caught only because the commit was verified rather than trusted.

Both are the same defect: **evidence that works for the person who does not need
it.** A record resolves on the author's machine; a hash verifies on the author's
machine; neither does anything for the auditor, who is the only reader that matters.

**Rules.**

- After publishing a hash for a tracked file, verify the hash of the COMMITTED
  BLOB, not the worktree file. `git cat-file -p HEAD:<path>` is the artifact a
  reader receives.
- Mark anything whose bytes ARE the claim as `-text`. Line-ending normalization is
  a content transform applied by default to everything the repository calls text --
  correct for source, silently wrong for signed material, hashed evidence, and
  fixtures pinned by digest. It is invisible in a diff and sits underneath every
  integrity claim in the repository.
- **A tier-1 reuse block is recorded but not validated.** Any evidence claim living
  in one is unchecked prose until the entry is promoted. Widening tier-1
  enforcement was deliberately NOT done as part of this fix: tightening a validator
  against existing history without first enumerating what breaks is the b0de2fe
  mistake, and this register already carries it as CF-1.

### CF-9 - A gate that checks a review happened, not what it concluded

The provenance anchor's ADR-18 tier-2 reuse review was performed on 2026-08-29 by
9 distinct reviewers across 7 surfaces. Its outcome was REVISION REQUIRED: four
confirmed defects, two of them reproduced, plus a six-reviewer finding that the
ladder was not satisfied and a two-reviewer finding that the artifact's headline
claim is false.

Filling in the reuse block with that review makes `spec_gate --check` go green.

`_reviewer_problems` requires `surfaces`, `families`, `record`, `outcome` and
`date`; it checks that `outcome` is a non-empty string and never reads it. A
review that approved and a review that demanded revision are indistinguishable to
the gate. The `verdict` field is the ladder rung, not the outcome, so nothing in
the registry carries whether the review passed.

That is not a bug in the sense that the gate does what it says -- ADR-18 requires
an independent review to have occurred, and one did. It is a bug in what a green
gate *communicates*, which is the only thing a gate is for.

**Not fixed here, deliberately.** Teaching the gate an outcome vocabulary means
inventing one and enforcing it against every existing entry, which is the CF-1
mistake -- tightening a validator against existing history without enumerating
what breaks. Recorded as a proposal: a recognised negative outcome should emit a
warning, additive and fail-open, so a green run still says "reviewed, revision
outstanding" out loud.

**Rule:** when a gate passes on something you know is unresolved, say so in the
artifact itself. The anchor spec's status line now carries "spec_gate --check
passes on this entry. That is the gate reporting that a review happened, not that
it approved."

---

## 4. Insights worth keeping

1. **Undeniability beats impossibility.** You cannot stop a hole in a signed chain.
   You can make it arithmetically visible and enumerate it by exact sequence number.
2. **A signed artifact cannot be repaired.** Correcting a field breaks the signature.
   Any contract enforced against history is a contract that can permanently kill a
   chain, so enforcement belongs at authorship where a failure is actionable.
3. **Only a signature establishes a competing history.** Unsigned JSON naming an
   identity and a sequence is not an occupant, and treating it as one lets unrelated
   corruption escalate an enumerable gap into a fatal error.
4. **A negative gate can always be evaded by a word not on the list.** Require positive
   evidence with payload.
5. **Generic guards, not instance guards.** "Every key any entry uses must be declared"
   caught the next instance; "`tier` and `reuse` must be declared" would not have.
6. **An unstated limit reads as a guarantee.** The packet spec now names both confirmed
   attacks explicitly, because silence about them was itself a claim.
7. **A metric that never fires is not evidence of the thing it measures.** Before
   citing an agreement number, check whether disagreement was reachable. Six unanimous
   panels under adversarial instruction described the instrument, not the panels.
8. **A warning nothing reads is the same as no warning.** `E_CONSENT_GATE_UNRESOLVED`
   was generated correctly and returned on a dataclass field no caller touched.
   Surfacing it in the audit script immediately exposed 73 chain-gap warnings that had
   been produced and discarded for weeks.
9. **Verify the premise, not just the plan.** The most expensive kind of correct work
   is work that is correct against a false premise, and the premise is the one part
   nobody re-reads once implementation starts.
10. **A diagnostic nobody publishes is a diagnostic you invented.** Before shipping
    a bespoke metric, check what the field reports for the same property. The
    hand-rolled similarity-floor check found a real defect; `n_eff` and the
    co-failure rate are what a reader can compare against somebody else's number.

---

## 5. What none of this fixed

Every entry above is a validator refinement. The finding all four external audits rated
Critical is untouched by all of them:

> **Wholesale head truncation.** Delete every packet above sequence *n* and present *n*
> as current. Enumeration finds gaps only relative to the highest sequence still
> present, so there is no gap to find. Nothing inside a self-signed chain distinguishes
> truncation from an agent that has not written since *n*.

Fourteen commits of hardening do not move it. The missing primitive is an external
anchor — something outside the packet store that witnesses what the store contained.
Until one exists, every integrity claim in this subsystem is scoped to a
buggy-but-honest writer, and "governed claim" overstates what the gate provides.

The second-order lesson, and the reason this register exists: **a fast local review
loop optimises the mechanism in front of it and will not tell you the mechanism is the
wrong one.** Eleven rounds of true findings, all real, none of them the thing that
mattered most.
