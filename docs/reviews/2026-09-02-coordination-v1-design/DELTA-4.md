# Delta 4 — the merge is not in the repo, and the block is over-scoped

**Targets:** `docs/superpowers/plans/2026-09-02-coordination-v1.md` (Task 0, Global Constraints)
and the operator's working assumptions.
**Reviewer:** Claude Opus 5, Claude Code session, 2026-09-03
**Prior:** [`DELTA.md`](DELTA.md), [`DELTA-PLAN.md`](DELTA-PLAN.md), [`DELTA-PLAN-2.md`](DELTA-PLAN-2.md), [`DELTA-3.md`](DELTA-3.md)

**DELTA-3 was adjudicated well.** N1 (ref-name legality) is now fully specified — percent-encoding
with `.` and `%` escaped, `git check-ref-format` as the authority, `E_ILLEGAL_ID` distinguished
from `conflict`, `is_claim_blocked` failing closed. N2 moved the base to
`feat/coordination-room-rebased` and correctly deleted Task 5's cherry-pick as a consequence. N3
collapsed to one canonicalizer with the case rule split by kind — and the `casefold()` /
`Straße` note is a better answer than the one requested. N4, N5, N7 carried. **N6's `SHARED-INDEX`
rejection is correct and I withdraw it**: pure Git cannot distinguish "another agent is active in
this checkout" from "I am", and the falsification is the right way to have closed it.

Two findings remain, both about state rather than text.

---

## M1 — The coordination-room-to-`main` merge is not present in this repository ❌ Blocked

The operator reports that a reconciliation agent merged the old coordinator room into `main`
without a merge commit or PR. **No evidence of it exists here.** Checked 2026-09-03:

```
git rev-list --left-right --count origin/main...main   ->  241   0
git reflog main                                        ->  (empty)
```

Local `main` has **zero unique commits** and is **241 behind `origin/main`**. Its reflog is empty,
so the branch pointer has not moved in this clone at all. Nothing was merged into it.

Content check on both:

| ref | `packages/coordination_room/` | `hook_pre_write._repo_relative` | `7334` in `start_mcp_daemons.ps1` |
|---|---|---|---|
| `main` | absent | absent | 0 hits |
| `origin/main` | absent | absent | 0 hits |

No merge is in progress either — `MERGE_HEAD` is unset in all 20 worktrees. The most recent branch
activity is `review/2026-09-03-pr-thread-fixround` (37 min) and `feat/coordination-room` (3 h,
Hermes's `c1a08f1`); neither is a room-into-`main` merge.

**Two things follow.**

1. **Do not plan on `main` carrying the room.** The base decision from N2
   (`feat/coordination-room-rebased`) stands unchanged, and for the same reason: it is the only
   branch carrying both `_repo_relative` and the `:7334` wiring.
2. **Local `main` is itself a hazard.** Anything branched from it starts 241 commits stale,
   silently. It should be fast-forwarded to `origin/main` or deleted locally, and the derived
   status view should flag a local branch that is far behind its upstream with nothing unique —
   that is a cheap panel and this is the motivating case.

The wider point: an agent's report of a durable action is not evidence the action landed. This is
the same class as the manifest-versus-deployment error corrected in DELTA-3's predecessors, one
level up — the report describes intent, the refs describe state, and only the second is checkable.

## M2 — Task 0's "no waiver path" blocks more than the gate requires ⚠️ Specified

The blocker is real. Verified:

- `packages/activity_log/provenance.py:1414` — `entry_has_consent()` checks only that
  `consent_ref.decision_action_hash` is a **non-empty string**. Its own docstring says so: *"no
  lookup against a real ConsentDecision action, no existence check, no signature check … the word
  'governed' in this codebase means 'carries a consent-shaped field', not 'was consented to'."*
- ADR-12 confirms the anchor is undefined, and
  `docs/agent-memory/project/adr19-ratification-deferred-to-consent-gate.md` prohibits substituting
  a commit SHA, session id, or placeholder. That prohibition is right and should hold.

**But the hard block is narrower than Task 0 assumes.** `_is_governed_claim`
(`packages/metacoordinator_mcp/tools.py`) returns True only for:

```python
blast_radius in {SYSTEM, SUBSTRATE} and proposal_type in {ADR_CHANGE, CONFIG_CHANGE, SPEC_CHANGE}
```

A **Module** blast radius does not reach the provenance requirement at all.

Now weigh M1 against that. M1 is a new read-only script plus a rendered section in a probe: no
claims, no enforcement, no new interface for other components, nothing written anywhere,
reversible by deleting one file. The design's `System` radius comes from the **claims** half —
`refs/agent-claims/*` plus hook enforcement — which genuinely alters an interface others depend on.
Gating a read-only status view behind an unratified Substrate-level consent anchor is a scope
mismatch, and it blocks precisely the piece that four independent reviews put first because it is
the reach-maximizing, lowest-risk one.

**Two legitimate paths, neither of which fakes the anchor:**

1. **Split the claim by blast radius.** Submit M1 as `Module` / `SpecChange` — it does not hit the
   provenance hard-block, so it can go through the real consensus gate today, with a real round and
   a real recorded decision. Submit M2/M3 as `System` and leave them blocked on ADR-12. This is
   honest gating, not a bypass: the smaller change genuinely has the smaller radius.
2. **An operator waiver for the docs-level decision**, recorded in this directory. The earlier plan
   draft allowed exactly this ("APPROVED **or** a written operator waiver"); the current Task 0
   removed it. Note what the removal actually accomplishes: since `entry_has_consent` admits any
   non-empty string, the block on Task 0 is a **policy** the operator owns, not a **mechanism** the
   code enforces. Hardening it to "no waiver path" makes the block stricter than the gate it cites,
   and the operator is the only party who can lift a policy they set.

**Recommendation:** path 1. It unblocks M1 through the real gate at its real radius, keeps M2/M3
correctly blocked until ADR-12 lands, and requires nobody to type a hash that means nothing.

**What must not change:** no placeholder anchor, and M2/M3 stay blocked. The prohibition in the
memory note is correct and this delta does not touch it.

---

## Summary

| # | Finding | Severity |
|---|---|---|
| M1 | the reported room-to-`main` merge is absent; local `main` is 241 behind with 0 unique | blocking |
| M2 | Task 0 blocks M1 at a radius M1 does not have; `Module` escapes the provenance gate | scope |

M1 changes nothing about the plan's base (N2 already chose correctly) but does change what anyone
can assume about `main`. M2 is worth a decision this session: M1 is the piece everyone agreed to
ship first, and it is currently blocked by the half of the design it does not belong to.
