# Scale mismatch is the recurring defect

**Date:** 2026-08-26
**Status:** ✅ Verified — seven instances from one session, each independently found and fixed
**Related:** [`finite-steps-share-the-flow.md`](finite-steps-share-the-flow.md), `docs/research/2026-08-25-provenance-failure-mode-register.md`

## Insight

Every defect found in the 2026-08-25/26 provenance-and-ensemble session has the same
shape: **the property lives at one scale and the check runs at another.** Not a
metaphor — seven instances, all fixed, all with commits.

| Defect | Property lives at | Check ran at |
|---|---|---|
| KERI/CESR divergence | byte encoding | field names |
| Ensemble "unanimity" | claim / position | whole response |
| Reuse gate never fired | design decision | artifact registration |
| FM-4 (fix one reader, miss its sibling) | structure | instance |
| Consent gate | resolved record | non-empty string |
| Head truncation | packet **set** | per-identity chain |
| CI break I caused | full green set | the subset I ran |

The failure is invisible from inside the check. A measurement at the wrong scale
does not return "unknown" — it returns a *confident wrong answer*. Whole-response
cosine similarity did not report low confidence; it reported 100% consensus, six
times, on prompts written to provoke dissent.

## Rule

For any check, name **both** scales explicitly: where the property lives, and
where you are measuring. If they differ, the check is decorative regardless of
how rigorous it looks. This is cheap to ask and catches the whole class.

The corollary is the anchor's design argument in one line: sequence gaps operate
at chain scale, truncation attacks set scale, therefore no amount of gap
enumeration can ever see it. Adding a commitment at set scale was not a better
version of the same check — it was the first check at the right scale.

## Do not

Treat this as cosmology. The useful claim is narrow and operational: **scale is a
property of a measurement, and mismatched measurements fail silently.** It does
not need a new framework, and the frames-of-scale / nested-observer material
already in canon is where the general version lives.
