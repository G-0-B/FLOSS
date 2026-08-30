"""Measure how many independent reviewers a review panel actually contained.

    python scripts/review_independence.py reviews/*.json
    python scripts/review_independence.py --adjudication reviews/verdicts.json reviews/*.json

Reads reviewer outputs in the schema from
`docs/governance/manual-review-protocol-v1.0.md` and reports the Kish effective
sample size over the panel.

WHY

Kohli, arXiv:2605.29800, measured 9 frontier LLM judges from 7 model families and
found they carried the information of about 2.18 independent votes: the best
single judge matched or beat the whole panel on every dataset, restricting to one
judge per family made independence WORSE (n_eff 1.93), and better aggregation
closed at most 11% of the gap even with oracle labels. The paper recommends
computing n_eff as a standard panel diagnostic, treating n_eff/k < 0.5 as cause
for caution.

    n_eff = k / (1 + (k - 1) * mean_pairwise_phi)

DEVIATION FROM THE SOURCE METHOD -- READ THIS BEFORE CITING ANY NUMBER

The paper builds each judge's binary vector from ERRORS against gold labels. This
project reviews unresolvable architecture questions and has no gold labels, so
the item set here is the UNION OF FINDINGS RAISED and each reviewer's vector is
"did you raise this one".

That measures REDUNDANCY, not accuracy. It answers "how many distinct
perspectives did I pay for", never "how often were they right". Two consequences
that must not be forgotten:

  * A reviewer who raises nothing looks maximally independent. Solo-find counts
    and finding totals are reported alongside n_eff for exactly this reason --
    n_eff alone is not interpretable.
  * Correlation over findings-raised cannot see the co-failure tail. Chen,
    arXiv:2606.27288, proves mean pairwise correlation cannot identify beta, the
    rate at which every reviewer is wrong together, and beta is what actually
    bounds the achievable gain. The one thing this tool cannot measure is the
    thing nobody found. Fill that in retrospectively via --adjudication.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

CAUTION_RATIO = 0.5  # arXiv:2605.29800's recommended threshold


class NotAReview(ValueError):
    """The file is valid JSON but is not a reviewer output."""


def load_review(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    # A directory of reviews also holds manifests, merge maps and adjudications.
    # Crashing on the first one that is not a review makes a glob unusable and
    # tells the caller nothing about which file was wrong.
    if not isinstance(document, dict) or "reviewer" not in document:
        raise NotAReview(
            f"no `reviewer` object (top level is "
            f"{type(document).__name__}); not a reviewer output"
        )
    reviewer = document.get("reviewer") or {}
    # Labelled by SELECTED model and harness. Never by the self-reported name:
    # a model has no introspective access to its own deployment identity, so
    # `model_self_reported` is a claim to be recorded and disagreed with, not an
    # identifier. `model` is accepted as a legacy alias.
    selected = (
        reviewer.get("model_selected") or reviewer.get("model") or "?"
    )
    harness = reviewer.get("harness")
    label = f"{selected}@{harness}" if harness else (selected if selected != "?" else path.stem)
    return {
        "label": str(label),
        "path": path,
        "harness": harness,
        "self_reported": reviewer.get("model_self_reported"),
        "saw_prior": bool(reviewer.get("saw_prior_reviews")),
        "tools": [t for t in (reviewer.get("tools_used") or []) if t != "none"],
        "findings": document.get("findings") or [],
        "predicted_majority": document.get("predicted_majority"),
        "expects_to_be_alone": document.get("where_you_expect_to_be_alone"),
    }


def finding_key(finding: dict[str, Any]) -> str:
    """Identity of a finding ACROSS reviewers.

    Two reviewers describe the same defect in different words, so the id a
    reviewer assigns is useless for matching. `location` plus a normalized claim
    is the best available key without a human merge pass -- and a human merge
    pass is the right answer when the numbers matter. `--merge` accepts one.
    """

    location = str(finding.get("location") or "").strip().lower()
    claim = " ".join(str(finding.get("claim") or "").lower().split())
    return f"{location}::{claim}" if location else claim


def apply_merge(
    reviews: list[dict], merge_map: dict[str, str]
) -> None:
    """Rewrite finding keys through an operator-supplied equivalence map."""

    for review in reviews:
        for finding in review["findings"]:
            key = finding_key(finding)
            finding["_key"] = merge_map.get(key, key)


def phi(a: list[int], b: list[int]) -> float:
    """Pearson correlation of two binary vectors (the phi coefficient)."""

    n = len(a)
    if n == 0:
        return 0.0
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((y - mean_b) ** 2 for y in b)
    if var_a == 0 or var_b == 0:
        # A reviewer who raised everything, or nothing, has no variance and
        # therefore no measurable correlation with anyone. Returning 0.0 would
        # read as "independent", which is exactly backwards for the raised-
        # everything case, so the caller flags these separately.
        return float("nan")
    return cov / math.sqrt(var_a * var_b)


def kish_neff(vectors: list[list[int]]) -> tuple[float, float, int]:
    """Return (n_eff, mean_phi, comparable_pair_count)."""

    k = len(vectors)
    if k < 2:
        return float(k), 0.0, 0
    values = []
    for i in range(k):
        for j in range(i + 1, k):
            value = phi(vectors[i], vectors[j])
            if not math.isnan(value):
                values.append(value)
    if not values:
        return float("nan"), float("nan"), 0
    mean_phi = sum(values) / len(values)
    if mean_phi <= 0:
        # Kish assumes non-negative mean correlation. Below zero the formula
        # still returns a finite number and that number is garbage: on the
        # first real corpus, phi_bar = -0.096 with k = 10 produced
        # n_eff = 71.33 and an "independence ratio" of 713%, printed as if it
        # were a result.
        #
        # A negative mean here almost never means the reviewers are genuinely
        # anti-correlated. It means the finding sets are near-disjoint, which
        # makes the binary vectors anti-correlated by construction -- and
        # near-disjoint sets are what a naive text matcher produces when
        # reviewers word the same defect differently. The matcher is the
        # suspect, not the panel.
        return float("nan"), mean_phi, len(values)
    denominator = 1 + (k - 1) * mean_phi
    if denominator <= 0:
        return float("nan"), mean_phi, len(values)
    return k / denominator, mean_phi, len(values)


def power_iteration_max_eigenvalue(matrix: list[list[float]], steps: int = 500) -> float:
    """Largest eigenvalue of a symmetric matrix, for the n_eff = k/lambda_max check.

    Power iteration rather than numpy: this repository declares no numeric stack,
    and adding one for a k x k matrix where k is under ten would be its own
    reuse-gate violation.
    """

    k = len(matrix)
    if k == 0:
        return float("nan")
    vector = [1.0] * k
    value = 0.0
    for _ in range(steps):
        product = [sum(matrix[i][j] * vector[j] for j in range(k)) for i in range(k)]
        norm = math.sqrt(sum(x * x for x in product))
        if norm == 0:
            return float("nan")
        vector = [x / norm for x in product]
        value = norm
    return value


def build_matrix(reviews: list[dict]) -> tuple[list[str], list[list[int]]]:
    keys: list[str] = []
    seen: set[str] = set()
    for review in reviews:
        for finding in review["findings"]:
            key = finding.get("_key") or finding_key(finding)
            if key and key not in seen:
                seen.add(key)
                keys.append(key)
    vectors = []
    for review in reviews:
        raised = {
            finding.get("_key") or finding_key(finding)
            for finding in review["findings"]
        }
        vectors.append([1 if key in raised else 0 for key in keys])
    return keys, vectors


def report(reviews: list[dict], adjudication: dict[str, Any] | None) -> int:
    # A reviewer who raised nothing has no variance, so it contributes no
    # pairwise phi -- but it still counts toward k, and k appears in the
    # numerator of the Kish formula. A null reviewer therefore INFLATES n_eff
    # and flatters the panel. The docstring named this risk; a named risk with
    # no guard is how every other defect in this repository started.
    empty = [review for review in reviews if not review["findings"]]
    if empty:
        for review in empty:
            print(
                f"excluding {review['label']}: no findings. A reviewer who "
                f"raised nothing cannot be correlated with anyone and would "
                f"raise n_eff by sitting in k.",
                file=sys.stderr,
            )
        reviews = [review for review in reviews if review["findings"]]

    keys, vectors = build_matrix(reviews)
    k = len(reviews)
    if k < 2:
        print("Need at least two reviews to measure independence.")
        return 2
    if not keys:
        print("No findings across any review; nothing to measure.")
        return 2

    n_eff, mean_phi, pairs = kish_neff(vectors)
    # How much of the finding set was raised by more than one reviewer. If this
    # is near zero the overlap matrix carries no signal and nothing downstream
    # of it means anything, whatever the arithmetic produces.
    overlap_counts = [sum(v[i] for v in vectors) for i in range(len(keys))]
    shared_findings = sum(1 for c in overlap_counts if c > 1)
    overlap_rate = shared_findings / len(keys) if keys else 0.0
    correlation = [
        [1.0 if i == j else (0.0 if math.isnan(phi(vectors[i], vectors[j]))
                             else phi(vectors[i], vectors[j]))
         for j in range(k)]
        for i in range(k)
    ]
    lambda_max = power_iteration_max_eigenvalue(correlation)
    eigen_neff = k / lambda_max if lambda_max and not math.isnan(lambda_max) else float("nan")

    print(f"Reviewers (k):        {k}")
    print(f"Distinct findings:    {len(keys)}")
    print(f"Comparable pairs:     {pairs} of {k * (k - 1) // 2}")
    print(f"Mean pairwise phi:    {mean_phi:.3f}")
    print(
        f"Findings raised by >1: {shared_findings} of {len(keys)} "
        f"({overlap_rate:.0%})"
    )

    if math.isnan(n_eff):
        print()
        print("n_eff:                REFUSED — not computable on this input")
        print(
            f"  Mean pairwise phi is {mean_phi:+.3f}. Kish assumes a "
            f"non-negative mean; below zero the formula returns a finite "
            f"number that is meaningless."
        )
        print(
            f"  Almost certainly the MATCHER, not the panel: only "
            f"{overlap_rate:.0%} of findings were raised by more than one "
            f"reviewer, and near-disjoint sets are anti-correlated by "
            f"construction. Reviewers word the same defect differently."
        )
        print("  Do a human merge pass and re-run with --merge.")
        REFUSED = True
    else:
        REFUSED = False
        print(f"n_eff (Kish):         {n_eff:.2f}")
        print(f"n_eff (eigenvalue):   {eigen_neff:.2f}")
        ratio = n_eff / k if k else float("nan")
        print(f"Independence ratio:   {ratio:.1%}")
        if overlap_rate < 0.25:
            print(
                f"  ^ TREAT AS UNRELIABLE: only {overlap_rate:.0%} of findings "
                f"were raised by more than one reviewer, so the overlap matrix "
                f"is mostly zeros and n_eff is dominated by matching failures."
            )
        elif ratio < CAUTION_RATIO:
            print(
                f"  ^ below the {CAUTION_RATIO:.0%} caution threshold "
                f"(arXiv:2605.29800): you paid for {k} perspectives and "
                f"received about {n_eff:.1f}."
            )
    print()

    # Solo-find is defined by the protocol as findings only this reviewer raised
    # THAT SURVIVED ADJUDICATION. Computed from the raw vectors alone, a unique
    # finding the operator REJECTED still counted toward that reviewer's value --
    # overstating exactly the reviewers whose distinctiveness was being wrong.
    accepted_keys: set[str] | None = None
    if adjudication and isinstance(adjudication.get("accepted"), list):
        accepted_keys = {str(k) for k in adjudication["accepted"]}

    print("Per reviewer:")
    for index, review in enumerate(reviews):
        raised = sum(vectors[index])
        solo = sum(
            1
            for position in range(len(keys))
            if vectors[index][position] == 1
            and sum(v[position] for v in vectors) == 1
            and (accepted_keys is None or keys[position] in accepted_keys)
        )
        tools = ",".join(review["tools"]) or "none"
        cascade = " (cascade)" if review["saw_prior"] else ""
        label = "solo*" if accepted_keys is not None else "solo"
        print(
            f"  {review['label']:<38} raised {raised:>3}  {label} {solo:>3}  "
            f"tools[{tools}]{cascade}"
        )
    if accepted_keys is None:
        print(
            "  (solo counts are UNADJUDICATED: a unique finding later "
            "rejected still counts here. Supply --adjudication for the "
            "protocol's definition; adjudicated counts are marked solo*.)"
        )
    print()

    # Tool access is the hypothesis under test: if it decorrelates more than
    # family diversity does, the tooled reviewers should hold the lowest
    # pairwise correlations. Printed rather than concluded -- one run is an
    # anecdote.
    # Reviewers that share a harness are suspected of sharing an orchestrator,
    # whatever the dropdown said. Observed 2026-08-29: several nominally
    # different models on one harness all self-reported the same identity, and
    # one vendor's stated version disagreed with what its models claimed. A
    # model has no introspective access to its own deployment identity, so a
    # self-report is a claim; the phi below is the measurement.
    by_harness: dict[Any, list[str]] = {}
    for review in reviews:
        if review.get("harness"):
            by_harness.setdefault(review["harness"], []).append(review["label"])
    shared = {h: labels for h, labels in by_harness.items() if len(labels) > 1}
    if shared:
        print("Reviewers sharing a harness (independence is a property of the")
        print("harness, not of the model name on the dropdown):")
        for harness, labels in shared.items():
            print(f"  {harness}: {', '.join(labels)}")
        print("  ^ if their pairwise phi below is near 1.0 they are one reviewer.")
        print()

    reported = {
        review["label"]: review["self_reported"]
        for review in reviews
        if review.get("self_reported")
    }
    collisions = {}
    for label, claimed in reported.items():
        collisions.setdefault(claimed, []).append(label)
    disputed = {c: ls for c, ls in collisions.items() if len(ls) > 1}
    if disputed:
        print("Identity collisions (self-reported, NOT verified):")
        for claimed, labels in disputed.items():
            print(f"  {claimed!r} claimed by: {', '.join(labels)}")
        print(
            "  ^ weak evidence about training corpora, no evidence about "
            "routing. Fingerprint behaviour rather than asking."
        )
        print()

    print("Pairwise phi (lower = more independent):")
    ordered = sorted(
        (
            (correlation[i][j], reviews[i]["label"], reviews[j]["label"])
            for i in range(k)
            for j in range(i + 1, k)
        )
    )
    for value, left, right in ordered:
        print(f"  {value:+.3f}  {left}  x  {right}")

    if adjudication:
        print()
        accepted = adjudication.get("accepted") or []
        missed = adjudication.get("missed_by_all") or []
        print(f"Adjudicated accepted: {len(accepted)}")
        print(f"Missed by every reviewer (beta proxy): {len(missed)}")
        if missed:
            print(
                "  ^ pairwise correlation provably cannot predict these "
                "(arXiv:2606.27288). They are the ceiling on what any panel "
                "of these reviewers could have delivered."
            )
            for item in missed:
                print(f"    - {item}")
    else:
        print()
        print(
            "No --adjudication supplied, so the co-failure tail is unmeasured. "
            "n_eff describes redundancy among findings that were raised; it says "
            "nothing about what everyone missed."
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reviews", nargs="+", type=Path)
    parser.add_argument(
        "--merge",
        type=Path,
        default=None,
        help=(
            "JSON object mapping a finding key to a canonical key, for the "
            "human merge pass. Two reviewers word the same defect differently "
            "and automatic matching will undercount overlap -- which inflates "
            "n_eff and flatters the panel."
        ),
    )
    parser.add_argument(
        "--adjudication",
        type=Path,
        default=None,
        help=(
            'JSON with {"accepted": [...], "missed_by_all": [...]} from Lane C, '
            "to report the co-failure tail n_eff cannot see."
        ),
    )
    args = parser.parse_args(argv)

    reviews = []
    for path in args.reviews:
        try:
            reviews.append(load_review(path))
        except (OSError, json.JSONDecodeError, NotAReview) as exc:
            print(f"skipping {path}: {exc}", file=sys.stderr)
    if not reviews:
        print("no readable reviews", file=sys.stderr)
        return 2

    merge_map: dict[str, str] = {}
    if args.merge:
        merge_map = json.loads(args.merge.read_text(encoding="utf-8"))
    apply_merge(reviews, merge_map)

    adjudication = None
    if args.adjudication:
        adjudication = json.loads(args.adjudication.read_text(encoding="utf-8"))

    return report(reviews, adjudication)


if __name__ == "__main__":
    raise SystemExit(main())
